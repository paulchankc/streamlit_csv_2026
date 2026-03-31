# app.py
import streamlit as st
import pandas as pd
import numpy as np
from dataclasses import dataclass
import io

@dataclass
class Geo_EO:
    file_path: str
    EO_filepath: str = '_EO.csv'
    output_filepath: str = 'Merged_EO.csv'
    
    def read_csv_TypeA(self):
        column_A = ['Photo Name', 'Time', 'Easting', 'Northing', 'Height', 'Omega', 'Phi', 'Kappa',
                    'M11', 'M21', 'M31','M12', 'M22','M32', 'M13', 'M23','M33']
        df = pd.read_csv(self.file_path, names=column_A, delimiter=';')
        return df
    
    def read_csv_TypeB(self):
        df = pd.read_csv(self.file_path, header=0, delimiter=';')
        df1 = df[['Image filename', 'Time', 'X1', 'Y1', 'Z1', 'Omega', 'Phi', 'Kappa',
                  'M11', 'M21', 'M31','M12', 'M22','M32', 'M13', 'M23','M33']]
        df1 = df1.rename(columns={'Image filename': 'Photo Name', 'X1': 'Easting', 
                                   'Y1': 'Northing', 'Z1': 'Height'})
        return df1

    def calculate_angles(self, df):
        df['Omega'] = np.arctan2(-df['M12'], df['M11']) * 180 / np.pi
        df['Phi'] = -90 - np.arctan2(-df['M23'], df['M33']) * 180 / np.pi
        df['Kappa'] = np.arcsin(-df['M13']) * 180 / np.pi
        return df[['Photo Name', 'Easting', 'Northing', 'Height', 'Omega', 'Phi', 'Kappa']]
    
    def merge_with_EO(self, angles_df):
        df2 = pd.read_csv(self.EO_filepath, header=0)
        df2 = df2[['Photo Name', 'Date']]
        merged_df = pd.merge(df2, angles_df, on='Photo Name')
        merged_df = merged_df[['Photo Name', 'Date', 'Easting', 'Northing', 
                               'Height', 'Omega', 'Phi', 'Kappa']]
        merged_df.to_csv(self.output_filepath, index=False)
        return merged_df

def process_files(external_file, eo_file, file_type):
    """Process the uploaded files and return merged dataframe"""
    try:
        # Save uploaded files temporarily
        external_path = f"temp_external_{external_file.name}"
        eo_path = f"temp_eo_{eo_file.name}"
        
        with open(external_path, 'wb') as f:
            f.write(external_file.getbuffer())
        
        with open(eo_path, 'wb') as f:
            f.write(eo_file.getbuffer())
        
        # Process based on file type
        geo_eo = Geo_EO(external_path, EO_filepath=eo_path)
        
        if file_type == 'A':
            df = geo_eo.read_csv_TypeA()
        else:
            df = geo_eo.read_csv_TypeB()
        
        # Calculate angles and merge
        angles_df = geo_eo.calculate_angles(df)
        merged_df = geo_eo.merge_with_EO(angles_df)
        
        # Clean up temp files
        import os
        os.remove(external_path)
        os.remove(eo_path)
        os.remove(geo_eo.output_filepath)
        
        return merged_df, None
    
    except Exception as e:
        return None, str(e)

def main():
    # Page configuration
    st.set_page_config(
        page_title="External Orientation Processor",
        page_icon="📸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
        }
        .main-header p {
            color: rgba(255,255,255,0.9);
            margin-top: 0.5rem;
            font-size: 1.1rem;
        }
        .info-box {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin-bottom: 1rem;
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>📸 External Orientation Processor</h1>
            <p>Import CSV files, select format type, and merge with EO data</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 External Orientation CSV")
        external_file = st.file_uploader(
            "Upload External Orientation CSV file",
            type=['csv'],
            help="Upload the CSV file containing orientation data"
        )
        
        if external_file:
            st.success(f"✅ Uploaded: {external_file.name}")
    
    with col2:
        st.subheader("📁 _EO.csv File")
        eo_file = st.file_uploader(
            "Upload _EO.csv file",
            type=['csv'],
            help="Upload the EO CSV file containing Photo Name and Date"
        )
        
        if eo_file:
            st.success(f"✅ Uploaded: {eo_file.name}")
    
    # File type selection
    st.markdown("---")
    st.subheader("🔧 Configuration")
    
    file_type = st.radio(
        "Select File Type",
        options=['A', 'B'],
        format_func=lambda x: f"Type {x}",
        horizontal=True,
        help="Type A: Standard format without headers\nType B: Extended format with headers"
    )
    
    # Display format information
    with st.expander("📖 Format Information"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Type A Format (No headers):**")
            st.code("Photo Name;Time;Easting;Northing;Height;Omega;Phi;Kappa;M11;M21;M31;M12;M22;M32;M13;M23;M33")
            st.markdown("Columns are in fixed order without header row")
        
        with col2:
            st.markdown("**Type B Format (With headers):**")
            st.code("Image filename;Time;X1;Y1;Z1;Omega;Phi;Kappa;M11;M21;M31;M12;M22;M32;M13;M23;M33")
            st.markdown("First row contains column names")
        
        st.markdown("**_EO.csv Format:**")
        st.code("Photo Name,Date")
        st.markdown("CSV file with Photo Name and Date columns")
    
    # Process button
    st.markdown("---")
    
    if st.button("🚀 Process Files", type="primary", use_container_width=True):
        if external_file is None or eo_file is None:
            st.error("❌ Please upload both CSV files before processing")
        else:
            with st.spinner("Processing files..."):
                merged_df, error = process_files(external_file, eo_file, file_type)
                
                if error:
                    st.error(f"❌ Error processing files: {error}")
                else:
                    st.success("✅ Files processed successfully!")
                    
                    # Display statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Records", len(merged_df))
                    with col2:
                        st.metric("Columns", len(merged_df.columns))
                    with col3:
                        st.metric("File Type", f"Type {file_type}")
                    
                    # Display data preview
                    st.subheader("📊 Data Preview")
                    st.dataframe(
                        merged_df.head(10),
                        use_container_width=True,
                        height=400
                    )
                    
                    # Display data info
                    with st.expander("📈 Data Statistics"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Column Names:**")
                            st.write(merged_df.columns.tolist())
                        with col2:
                            st.write("**Data Types:**")
                            st.write(merged_df.dtypes.to_dict())
                    
                    # Download section
                    st.subheader("💾 Download Results")
                    
                    # Convert dataframe to CSV for download
                    csv_buffer = io.StringIO()
                    merged_df.to_csv(csv_buffer, index=False)
                    csv_string = csv_buffer.getvalue()
                    
                    st.download_button(
                        label="📥 Download Merged CSV",
                        data=csv_string,
                        file_name="Merged_EO.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    # Option to show all data
                    if st.checkbox("Show all data"):
                        st.dataframe(merged_df, use_container_width=True)

if __name__ == "__main__":
    main()