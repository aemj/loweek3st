import streamlit as st
from agents import Agent, FileSearchTool, Runner, WebSearchTool
import asyncio
import os
from config import config

# Function to load agent instructions from file
def load_agent_instructions():
    """Load agent instructions from agent_instructions.txt file."""
    try:
        with open("agent_instructions.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback instructions if file not found
        return "You are a research assistant who helps users find information using available search tools. Always cite your sources."

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide"
)

# Title
st.title(f"{config.APP_ICON} {config.APP_TITLE}")
st.markdown("Ask questions about your uploaded documents or search the web for information.")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Get environment status
    env_status = config.get_env_status()
    
    # Display status
    if env_status["openai_key_set"]:
        st.success("✅ OpenAI API Key loaded from .env")
    else:
        st.error("❌ OpenAI API Key not found in .env")
    
    if env_status["vector_store_set"]:
        st.success("✅ Vector Store ID loaded from .env")
    else:
        st.error("❌ Vector Store ID not found in .env")
    
    st.markdown("---")
    
    # Search Configuration
    st.header("🔍 Search Sources")
    
    use_web_search = st.checkbox(
        "Web Search",
        value=config.ENABLE_WEB_SEARCH_DEFAULT,
        help="Enable searching the web for information"
    )
    
    use_document_search = st.checkbox(
        "Document Search",
        value=config.ENABLE_DOCUMENT_SEARCH_DEFAULT,
        help="Enable searching uploaded documents"
    )
    
    if not use_web_search and not use_document_search:
        st.warning("⚠️ At least one search source must be enabled")
    
    # Document search settings
    if use_document_search:
        with st.expander("Document Search Settings"):
            max_results = st.slider(
                "Max Results",
                min_value=1,
                max_value=10,
                value=config.MAX_RESULTS_DEFAULT,
                help="Maximum number of document results to retrieve"
            )
    else:
        max_results = config.MAX_RESULTS_DEFAULT
    
    st.markdown("---")
    
    # Display active sources
    st.subheader("Active Sources:")
    if use_web_search:
        st.markdown("🌐 Web Search")
    if use_document_search:
        st.markdown("📄 Document Search")
    if not use_web_search and not use_document_search:
        st.markdown("❌ No sources enabled")
    
    st.markdown("---")
    
    # Agent Instructions Preview
    with st.expander("📋 View Agent Instructions"):
        instructions = load_agent_instructions()
        st.text_area(
            "Instructions loaded from agent_instructions.txt:",
            value=instructions,
            height=150,
            disabled=True
        )
        st.info("💡 Edit agent_instructions.txt to customize the agent behavior")
    
    st.markdown("---")
    st.info("💡 Add your credentials to a `.env` file:\n```\nOPENAI_API_KEY=your_key_here\nVECTOR_STORE_ID=your_id_here\n```")
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Display metadata if available
        if "metadata" in message:
            with st.expander("ℹ️ Search Info"):
                st.json(message["metadata"])

# Function to run the agent
async def run_agent(query, api_key, vs_id, enable_web, enable_docs, max_doc_results):
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Build tools list based on configuration
    tools = []
    sources_used = []
    
    if enable_web:
        tools.append(WebSearchTool())
        sources_used.append("web search")
    
    if enable_docs:
        if not vs_id:
            raise ValueError("Document search enabled but Vector Store ID is missing")
        tools.append(
            FileSearchTool(
                max_num_results=max_doc_results,
                vector_store_ids=[vs_id],
            )
        )
        sources_used.append("vector data store search")
    
    if not tools:
        raise ValueError("At least one search source must be enabled")

    # Load base instructions from agent_instructions.txt file
    instructions = load_agent_instructions()
    
    # Add dynamic context based on enabled sources
    if enable_docs and not enable_web:
        # Document-only mode - be very strict
        instructions += "\n\nCURRENT SESSION MODE: DOCUMENT-ONLY SEARCH. You can ONLY use information from the uploaded documents via vector search. Do NOT use any general knowledge, training data, or external information. If the answer is not in the documents, clearly state 'I don't have information about [topic] in the uploaded documents.'"
    elif enable_web and not enable_docs:
        # Web-only mode
        instructions += "\n\nCURRENT SESSION MODE: WEB-ONLY SEARCH. You can only use information from web search results."
    elif enable_web and enable_docs:
        # Both sources available
        instructions += "\n\nCURRENT SESSION MODE: HYBRID SEARCH. You have access to both document search and web search. Use both sources appropriately."
    
    # Add current sources info
    sources_text = " and ".join(sources_used)
    instructions += f"\n\nCURRENT ACTIVE SOURCES: {sources_text}"
    
    agent = Agent(
        name=config.AGENT_NAME,
        instructions=instructions,
        tools=tools,
        model=config.AGENT_MODEL
    )
    
    result = await Runner.run(agent, query)
    
    return {
        "response": result.final_output,
        "metadata": {
            "sources_enabled": sources_used,
            "web_search": enable_web,
            "document_search": enable_docs,
            "max_doc_results": max_doc_results if enable_docs else None
        }
    }

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Check if API key and vector store ID are provided
    if not config.OPENAI_API_KEY:
        st.error("Please add your OpenAI API Key to the .env file.")
    elif not config.VECTOR_STORE_ID and use_document_search:
        st.error("Please add your Vector Store ID to the .env file or disable Document Search.")
    elif not use_web_search and not use_document_search:
        st.error("Please enable at least one search source in the sidebar.")
    else:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                result = asyncio.run(
                    run_agent(
                        prompt, 
                        config.OPENAI_API_KEY, 
                        config.VECTOR_STORE_ID,
                        use_web_search,
                        use_document_search,
                        max_results
                    )
                )
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": result["response"],
                    "metadata": result["metadata"]
                })
                st.rerun()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg
                })
                st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Built with Streamlit and OpenAI Agents</p>
    </div>
    """,
    unsafe_allow_html=True
)
