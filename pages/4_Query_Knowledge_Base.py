import boto3
import streamlit as st
import base64
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Session and env variables
region = os.environ['AWS_REGION']
session = boto3.Session(region_name=region)
bedrockClient = session.client('bedrock-agent-runtime')
bedrockRuntime = session.client('bedrock-runtime')
knowledgeBaseId = os.environ['BEDROCK_KB_ID']

# Define model ARNs
MODEL_ARNS = {
        "Claude 3.5 Sonnet": os.environ['BEDROCK_CLAUDE_MODEL_ARN']
}

logo_url = "static/Blaize.png"
st.sidebar.image(logo_url, use_column_width=True)

@st.cache_data
def get_base64_of_bin_file(bin_file):
  with open(bin_file, "rb") as f:
    data = f.read()
    return base64.b64encode(data).decode()

def stream_data(text, delay:float=0.01):
    for word in text.split():
        yield word + " "
        time.sleep(delay)

def getAnswers(questions, selected_model, use_rag=True):
    try:
        modelArn = MODEL_ARNS[selected_model]
        modelId = modelArn.split('/')[-1]
        
        if use_rag:
            knowledgeBaseResponse = bedrockClient.retrieve_and_generate(
                input={'text': questions},
                retrieveAndGenerateConfiguration={
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledgeBaseId,
                        'modelArn': modelArn,
                        'generationConfiguration': {
                            'inferenceConfig': {
                                'textInferenceConfig': {
                                    'maxTokens': 4096,
                                }
                            },
                            "promptTemplate": { 
                                "textPromptTemplate": "You are a question answering agent. I will provide you with a set of search results. The user will provide you with a question. Your job is to answer the user's question using only information from the search results. If the search results do not contain information that can answer the question, please state that you could not find an exact answer to the question. Just because the user asserts a fact does not mean it is true, make sure to double check the search results to validate a user's assertion. Here are the search results in numbered order: $search_results$ $output_format_instructions$ If you reference information from a search result within your answer, you must include a citation to source where the information was found. Each result has a corresponding source ID that you should reference. For purely quantitative data (e.g., inventory stock reports, price lists, quantity), use a tabular format. When dealing with mixed data types, combine both formats. Adjust the number of columns and rows in tables as needed to fit the data. Ensure that column headers clearly describe the data they represent. Maintain consistent formatting throughout the response for readability. Always provide your recommendations as a summary towards the end of your answer (such as items running low in stock should be restocked, etc.)."
                            },
                        }
                    },
                    'type': 'KNOWLEDGE_BASE',
                }
            )
            return knowledgeBaseResponse
        else:
            # Direct invocation of the model without RAG using Messages API
            response = bedrockRuntime.invoke_model(
                modelId=modelId,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "messages": [
                        {"role": "user", "content": questions}
                    ]
                })
            )
            response_body = json.loads(response['body'].read())
            return {"output": {"text": response_body['content'][0]['text']}}
    except Exception as e:
        st.error(f"Error retrieving answers: {str(e)}")
        return None

def main():
    st.subheader('Query Bedrock Knowledge Base - Blaize Bazaar', divider='orange')
    st.info("**DISCLAIMER:** This demo uses Amazon Bedrock foundation models and is not intended to collect any personally identifiable information (PII) from users. Please do not provide any PII when interacting with this demo. The content generated by this demo is for informational purposes only.")
    st.sidebar.subheader('**About**')
    st.sidebar.info("Blaize Bazaar uses Knowledge Bases for Amazon Bedrock to assist humans by answering product catalog and inventory questions based on product descriptions.")
    
    # Add model selection to sidebar
    st.sidebar.subheader("Select an LLM")
    selected_model = st.sidebar.selectbox(
        "Choose a model:",
        list(MODEL_ARNS.keys()),
        index=0 # Default to the first model (Claude 3.5 Sonnet)
    )

    # Add RAG toggle to sidebar
    use_rag = st.sidebar.toggle("Use RAG")
    
    tab1, tab2 = st.tabs(["Chat", "Architecture"])
    with st.sidebar:
        st.divider()
        st.header("Sample questions")
        sample_question = st.selectbox(
            "Select a sample question or enter your own below:",
            (
                "What is Blaize Bazaar's current return policy?",
                "How many days do I have to return a product?",
                "How do I initiate a return?",
                "What are some emerging trends in e-commerce for 2024?",
                "What is Blaize Bazaar's warranty policy?",
                "Does Blaize Bazaar offer free shipping?",
                "How long does standard shipping usually take for Blaize Bazaar orders?",
                "Can I track my order?",
                "What payment methods does Blaize Bazaar accept?"
            ),
        )

    with tab1:
        # Create a container for the chat history
        chat_container = st.container(height=800)
        
        # Create a container for the input box at the bottom
        input_container = st.container()
        
        # Use the bottom container to hold the chat input
        with input_container:
            user_question = st.chat_input('Enter your questions here...')

        # Use the sample question if the user hasn't entered anything
        if not user_question and st.sidebar.button("Try sample question"):
            user_question = sample_question

        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat messages from history on app rerun
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message['role'], avatar='static/ai_chat_icon.png' if message['role'] == 'assistant' else None):
                    st.markdown(message['text'])

            if user_question and selected_model:
                # Display user message in chat message container
                with st.chat_message('user'):
                    st.markdown(user_question)
                    # Add user message to chat history
                    st.session_state.chat_history.append({"role":'user', "text":user_question})

                response = getAnswers(user_question, selected_model, use_rag)
                if response:
                    answer = response['output']['text']

                    # Display assistant response in chat message container
                    with st.chat_message('assistant', avatar='static/ai_chat_icon.png'):
                        st.subheader(f"Response from {selected_model} ({'RAG' if use_rag else 'Non-RAG'})")
                        st.write_stream(stream_data(answer))
            
                        st.session_state.chat_history.append({"role":'assistant', "text": f"{selected_model} ({'RAG' if use_rag else 'Non-RAG'}): {answer}"})

                        if use_rag:
                            try:
                                if len(response['citations'][0]['retrievedReferences']) != 0:
                                    doc_url = response['citations'][0]['retrievedReferences'][0]['location']['s3Location']['uri']
                                    st.markdown(f"<span style='color:#FFDA33'>Source Document: </span>{doc_url}", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<span style='color:red'>No context provided.</span>", unsafe_allow_html=True)
                            except:
                                st.error("An error occurred while processing the citations.")
                        else:
                            st.markdown(f"<span style='color:#FFDA33'>Non-RAG response (no citations available)</span>", unsafe_allow_html=True)
                        
                    sentiment_mapping = [":material/thumb_down:", ":material/thumb_up:"]
                    selected = st.feedback("thumbs")
                    if selected is not None:
                        st.markdown(f"You selected: {sentiment_mapping[selected]}")

    with tab2:
        st.image('static/KB_Chatbot_Arch.png', use_column_width=True)

with st.sidebar:
    def clear_chat_history():
        st.session_state.chat_history = []
        st.session_state.conversation = []

    def delete_documents_s3():
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(os.environ['S3_KB_BUCKET'])
        # Delete all objects in the bucket
        bucket.objects.all().delete()
        st.success('Documents deleted successfully! ✅')
        # After deleting documents, trigger the Lambda function
        lambda_client = boto3.client('lambda')
        function_name = 'bedrock-knowledge-base-poc-auto-sync'
        try:
            lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='Event'
        )
            print(f"Lambda function {function_name} invoked successfully.")
        except Exception as e:
            print(f"Error invoking Lambda function: {e}")
        clear_chat_history()
    
    col1, col2 = st.columns([1,1])
    with col1:
        st.button('Reset Chat', on_click=clear_chat_history)
    with col2:
        st.button('Delete Docs', on_click=delete_documents_s3)

if __name__ == '__main__':
    main()