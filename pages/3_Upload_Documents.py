import boto3
from datetime import datetime
import streamlit as st
import os
import pandas as pd
from streamlit_pdf_viewer import pdf_viewer
from dotenv import load_dotenv

# Load environment variables and set up configurations
load_dotenv()

# Create the S3 client
@st.cache_resource
def get_s3_client():
    return boto3.client('s3', region_name=os.environ.get('AWS_REGION'))

def process_file(document):
    name, extension = os.path.splitext(document.name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{name}_{timestamp}{extension}"
    return file_name

def upload_file(file_name, renamed_file_name):
    bucket_name = os.environ.get('S3_KB_BUCKET')
    s3_client = get_s3_client()
    try:
        # Upload file to an S3 object from the specified local path
        s3_client.upload_file(file_name, bucket_name, renamed_file_name)
        st.success(f"Successfully uploaded the file! ✅")
    except Exception as e:
        st.markdown(f"Error: {str(e)}")

def main():
    st.set_page_config(page_title="Upload Documents - Blaize Bazaar", page_icon="📄", layout="wide")
    st.subheader('Upload Documents to Bedrock Knowledge Base', divider='orange')
    
    logo_url = "static/Blaize.png"
    st.sidebar.image(logo_url, use_column_width=True)
    
    st.sidebar.title('**About**')
    st.sidebar.info("This page allows you to upload documents (PDF or CSV) to the Bedrock Knowledge Base for Blaize Bazaar.")
    
    st.write ("---")
    
    # Add version info
    st.sidebar.divider()
    st.sidebar.caption(f"""
    Version: 1.0.0
    Last Updated: {datetime.now().strftime('%Y-%m-%d')}
    """)

    document = st.file_uploader("Upload Documents (PDF or CSV)", type=['pdf', 'csv'], key='file')

    if document:
        with open(document.name, 'wb') as f:
            f.write(document.getbuffer())
        
        modified_file_name = process_file(document)
        upload_file(document.name, modified_file_name)

        # Preview the uploaded file
        with st.container():
            if document.type == 'application/pdf':
                binary_data = document.getvalue()
                pdf_viewer(input=binary_data)
            elif document.type == 'text/csv':
                df = pd.read_csv(document)
                st.dataframe(df, use_container_width=True)

    # Add some information about the upload process
    st.write("### How it works")
    st.write("""
    1. Select a PDF or CSV file using the file uploader above.
    2. The file will be processed and given a unique name based on the current timestamp.
    3. The file will be uploaded to our secure S3 bucket.
    4. For PDFs, you'll see a preview of the document below the upload section.
    5. For CSVs, you'll see a preview of the data in a table format.
    6. The uploaded document will be automatically added to our Bedrock Knowledge Base.
    """)

    st.write("### Important Notes")
    st.write("""
    - Ensure that the documents you upload do not contain sensitive or personal information.
    - Large files may take longer to upload and process.
    - Supported file types are PDF and CSV only.
    - If you encounter any issues during the upload process, please contact our workshop team.
    """)

if __name__ == "__main__":
    main()