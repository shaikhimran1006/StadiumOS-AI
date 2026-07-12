"""RAG (Retrieval-Augmented Generation) service using Vertex AI Search."""

import logging
from typing import Any

from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.exceptions import GoogleAPIError, NotFound
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.domain.interfaces.ai_services import IRAGService

logger = logging.getLogger(__name__)


class RAGService(IRAGService):
    """Service for Retrieval-Augmented Generation using Vertex AI Search.

    Provides knowledge base search, document indexing, and search app management
    for grounding AI responses in authoritative stadium information.
    """

    def __init__(self) -> None:
        self._search_client: discoveryengine.SearchServiceClient | None = None
        self._data_client: discoveryengine.DataStoreServiceClient | None = None
        self._initialized = False
        self._initialize()

    def _initialize(self) -> None:
        try:
            self._search_client = discoveryengine.SearchServiceClient()
            self._data_client = discoveryengine.DataStoreServiceClient()
            self._initialized = True
            logger.info("RAGService initialized")
        except Exception:
            logger.exception("Failed to initialize RAGService clients")
            self._initialized = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def search_knowledge_base(
        self,
        query: str,
        max_results: int = 5,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the stadium knowledge base for relevant information.

        Args:
            query: The search query.
            max_results: Maximum number of results to return.
            filters: Optional filter expressions (e.g., {'category': 'security'}).

        Returns:
            List of search results with content, scores, and metadata.
        """
        if not self._initialized or self._search_client is None:
            logger.warning("RAGService not initialized, returning empty results")
            return []

        serving_config = self._get_serving_config()

        search_request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=max_results,
        )

        if filters:
            filter_parts = [f'{k}="{v}"' for k, v in filters.items()]
            search_request.filter = " AND ".join(filter_parts)

        try:
            response = self._search_client.search(request=search_request)

            results: list[dict[str, Any]] = []
            for result in response.results:
                doc_data = result.document.data
                results.append({
                    "title": getattr(doc_data, "title", ""),
                    "content": self._extract_snippets(result),
                    "source": getattr(doc_data, "source", ""),
                    "score": result.relevance_score,
                    "metadata": dict(doc_data) if hasattr(doc_data, "__iter__") else {},
                })

            logger.info(
                "Knowledge base search returned %d results for query: %s",
                len(results),
                query[:50],
            )
            return results

        except NotFound:
            logger.error("Search app or data store not found")
            return []
        except GoogleAPIError as exc:
            logger.error("Knowledge base search failed: %s", exc)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def index_document(
        self,
        document_id: str,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Index a document into the knowledge base.

        Args:
            document_id: Unique identifier for the document.
            content: The document content to index.
            metadata: Optional metadata (category, source, etc.).

        Returns:
            Dict with indexing status and details.
        """
        if not self._initialized or self._data_client is None:
            raise RuntimeError("RAGService not initialized")

        parent = self._get_branch_name()

        document = discoveryengine.Document(
            id=document_id,
            content=discoveryengine.Document.Content(
                raw_text=content,
            ),
        )

        if metadata:
            document.metadata = {k: v for k, v in metadata.items()}

        try:
            request = discoveryengine.CreateDocumentRequest(
                parent=parent,
                document=document,
                document_id=document_id,
            )
            response = self._data_client.create_document(request=request)

            logger.info("Document indexed: %s", document_id)
            return {
                "status": "success",
                "document_id": document_id,
                "name": response.name if hasattr(response, "name") else document_id,
            }

        except GoogleAPIError as exc:
            logger.error("Document indexing failed for %s: %s", document_id, exc)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def create_search_app(
        self,
        app_name: str,
        data_store_id: str,
        industry_vertical: str = "GENERIC",
    ) -> dict[str, Any]:
        """Create a new Vertex AI Search application.

        Args:
            app_name: Display name for the search app.
            data_store_id: ID for the associated data store.
            industry_vertical: Industry vertical (GENERIC, MEDIA, etc.).

        Returns:
            Dict with search app creation details.
        """
        if not self._initialized or self._data_client is None:
            raise RuntimeError("RAGService not initialized")

        project_location = f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_REGION}"

        data_store = discoveryengine.DataStore(
            display_name=app_name,
            industry_vertical=discoveryengine.IndustryVertical.IndustryVerticalEnum(
                industry_vertical
            ),
            solution_types=[
                discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH,
            ],
        )

        try:
            create_request = discoveryengine.CreateDataStoreRequest(
                parent=project_location,
                data_store=data_store,
                data_store_id=data_store_id,
            )
            operation = self._data_client.create_data_store(request=create_request)
            result = operation.result(timeout=300)

            logger.info("Search app created: %s (%s)", app_name, data_store_id)
            return {
                "status": "success",
                "app_name": app_name,
                "data_store_id": data_store_id,
                "name": result.name if hasattr(result, "name") else data_store_id,
            }

        except GoogleAPIError as exc:
            logger.error("Search app creation failed: %s", exc)
            raise

    async def get_document(
        self,
        document_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve a specific document from the knowledge base.

        Args:
            document_id: The document identifier.

        Returns:
            Document data dict or None if not found.
        """
        if not self._initialized or self._data_client is None:
            return None

        name = f"{self._get_branch_name()}/documents/{document_id}"

        try:
            document = self._data_client.get_document(name=name)
            return {
                "id": document.id,
                "content": document.content.raw_text if document.content else "",
                "metadata": dict(document.metadata) if document.metadata else {},
            }
        except NotFound:
            logger.warning("Document not found: %s", document_id)
            return None
        except GoogleAPIError as exc:
            logger.error("Failed to get document %s: %s", document_id, exc)
            return None

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the knowledge base.

        Args:
            document_id: The document identifier to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not self._initialized or self._data_client is None:
            return False

        name = f"{self._get_branch_name()}/documents/{document_id}"

        try:
            self._data_client.delete_document(name=name)
            logger.info("Document deleted: %s", document_id)
            return True
        except NotFound:
            logger.warning("Document not found for deletion: %s", document_id)
            return False
        except GoogleAPIError as exc:
            logger.error("Failed to delete document %s: %s", document_id, exc)
            return False

    def _get_serving_config(self) -> str:
        project_id = settings.GCP_PROJECT_ID
        location = settings.GCP_REGION
        data_store_id = getattr(settings, "RAG_DATA_STORE_ID", "stadium-knowledge-base")
        serving_config_id = getattr(settings, "RAG_SERVING_CONFIG_ID", "default_config")
        return (
            f"projects/{project_id}/locations/{location}"
            f"/collections/default_collection"
            f"/dataStores/{data_store_id}"
            f"/servingConfigs/{serving_config_id}"
        )

    def _get_branch_name(self) -> str:
        project_id = settings.GCP_PROJECT_ID
        location = settings.GCP_REGION
        data_store_id = getattr(settings, "RAG_DATA_STORE_ID", "stadium-knowledge-base")
        return (
            f"projects/{project_id}/locations/{location}"
            f"/collections/default_collection"
            f"/dataStores/{data_store_id}"
            f"/branches/0"
        )

    def _extract_snippets(self, result: discoveryengine.SearchResult) -> str:
        snippets: list[str] = []
        if hasattr(result, "document") and result.document:
            doc = result.document
            if hasattr(doc, "snippets") and doc.snippets:
                for snippet in doc.snippets:
                    if hasattr(snippet, "snippet") and snippet.snippet:
                        snippets.append(snippet.snippet)
            elif doc.content and doc.content.raw_text:
                text = doc.content.raw_text
                snippets.append(text[:500] + ("..." if len(text) > 500 else ""))
        return "\n".join(snippets) if snippets else ""
