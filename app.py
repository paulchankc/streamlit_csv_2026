# app.py
import streamlit as st
import pandas as pd
import numpy as np
from dataclasses import dataclass
import io
import os

@dataclass
class Geo_EO:
    file_path: str
    EO_filepath: str = '_EO.csv'
    output_filepath: str = 'Merged_EO.csv'
    delimiter: str = ';'
    
    def read_csv_TypeA(self):
        column_A = ['Photo Name', 'Time', 'Easting', 'Northing', 'Height', 'Omega', 'Phi', 'Kappa',
                    'M11', 'M21', 'M31','M12', 'M22','M32', 'M13', 'M23','M33']
        df = pd.read_csv(self.file_path, names=column_A, delimiter=self.delimiter)
        return df
    
    def read_csv_TypeB(self):
        df = pd.read_csv(self.file_path, header=0, delimiter=self.delimiter)
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

def validate_csv_format(df, expected_columns, file_type):
    """Validate that CSV has expected columns"""
    if file_type == 'B':
        missing = set(expected_columns) - set(df.columns)
        if missing:
            return False, f"Missing columns: {missing}"
    return True, "Valid"

def process_files(external_file, eo_file, file_type, delimiter, selected_columns):
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
        geo_eo = Geo_EO(external_path, EO_filepath=eo_path, delimiter=delimiter)
        
        # Validate Type B format before processing
        if file_type == 'B':
            test_df = pd.read_csv(external_path, header=0, delimiter=delimiter, nrows=1)
            expected_columns = ['Image filename', 'Time', 'X1', 'Y1', 'Z1', 'Omega', 'Phi', 'Kappa',
                               'M11', 'M21', 'M31','M12', 'M22','M32', 'M13', 'M23','M33']
            is_valid, message = validate_csv_format(test_df, expected_columns, file_type)
            if not is_valid:
                raise ValueError(f"Invalid Type B format: {message}")
        
        if file_type == 'A':
            df = geo_eo.read_csv_TypeA()
        else:
            df = geo_eo.read_csv_TypeB()
        
        # Calculate angles and merge
        angles_df = geo_eo.calculate_angles(df)
        merged_df = geo_eo.merge_with_EO(angles_df)
        
        # Filter columns based on user selection
        if selected_columns:
            merged_df = merged_df[selected_columns]
        
        # Clean up temp files
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
    
    # Sidebar for additional settings
    with st.sidebar:
        st.subheader("⚙️ Advanced Settings")
        
        # Delimiter selection
        delimiter = st.selectbox(
            "CSV Delimiter",
            options=[';', ',', '\t', '|'],
            index=0,
            help="Select the delimiter used in your CSV files"
        )
        
        st.markdown("---")
        
        # Column selection for output
        st.subheader("📋 Select Output Columns")
        all_columns = ['Photo Name', 'Date', 'Easting', 'Northing', 'Height', 'Omega', 'Phi', 'Kappa']
        selected_columns = st.multiselect(
            "Choose columns to include in final output",
            options=all_columns,
            default=all_columns,
            help="Select which columns you want in the merged CSV file"
        )
        
        st.markdown("---")
        
        # Additional options
        st.subheader("🎨 Display Options")
        show_all_data = st.checkbox("Show all data after processing", value=False)
        show_statistics = st.checkbox("Show detailed statistics", value=True)
        
        st.markdown("---")
        
        # About section
        st.subheader("ℹ️ About")
        st.info(
            "This tool processes External Orientation CSV files, "
            "calculates angles from rotation matrices, and merges "
            "with EO data files."
        )
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 External Orientation CSV")
        external_file = st.file_uploader(
            "Upload External Orientation CSV file",
            type=['csv'],
            help="Upload the CSV file containing orientation data",
            key="external"
        )
        
        if external_file:
            st.success(f"✅ Uploaded: {external_file.name}")
            
            # Preview external file
            if st.checkbox("Preview External File", key="preview_external"):
                try:
                    if delimiter:
                        preview_df = pd.read_csv(external_file, delimiter=delimiter, nrows=5)
                        if file_type == 'A' and 'header' not in st.session_state:
                            st.info("Type A format: No headers expected - showing first 5 rows as data")
                        st.dataframe(preview_df, use_container_width=True)
                except Exception as e:
                    st.warning(f"Cannot preview file: {str(e)}")
    
    with col2:
        st.subheader("📁 _EO.csv File")
        eo_file = st.file_uploader(
            "Upload _EO.csv file",
            type=['csv'],
            help="Upload the EO CSV file containing Photo Name and Date",
            key="eo"
        )
        
        if eo_file:
            st.success(f"✅ Uploaded: {eo_file.name}")
            
            # Preview EO file
            if st.checkbox("Preview EO File", key="preview_eo"):
                try:
                    preview_df = pd.read_csv(eo_file, nrows=5)
                    st.dataframe(preview_df, use_container_width=True)
                except Exception as e:
                    st.warning(f"Cannot preview file: {str(e)}")
    
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
            st.markdown(f"**Current delimiter:** `{delimiter}`")
        
        with col2:
            st.markdown("**Type B Format (With headers):**")
            st.code(f"Image filename{delimiter}Time{delimiter}X1{delimiter}Y1{delimiter}Z1{delimiter}Omega{delimiter}Phi{delimiter}Kappa{delimiter}M11{delimiter}M21{delimiter}M31{delimiter}M12{delimiter}M22{delimiter}M32{delimiter}M13{delimiter}M23{delimiter}M33")
            st.markdown("First row contains column names")
            st.markdown(f"**Current delimiter:** `{delimiter}`")
        
        st.markdown("**_EO.csv Format:**")
        st.code("Photo Name,Date")
        st.markdown("CSV file with Photo Name and Date columns (comma delimiter)")
    
    # Process button
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_button = st.button("🚀 Process Files", type="primary", use_container_width=True)
    
    if process_button:
        if external_file is None or eo_file is None:
            st.error("❌ Please upload both CSV files before processing")
        elif not selected_columns:
            st.error("❌ Please select at least one column for output")
        else:
            with st.spinner("Processing files..."):
                merged_df, error = process_files(external_file, eo_file, file_type, delimiter, selected_columns)
                
                if error:
                    st.error(f"❌ Error processing files: {error}")
                else:
                    st.success("✅ Files processed successfully!")
                    
                    # Display statistics
                    if show_statistics:
                        st.subheader("📊 Processing Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Records", len(merged_df))
                        with col2:
                            st.metric("Columns Selected", len(merged_df.columns))
                        with col3:
                            st.metric("File Type", f"Type {file_type}")
                        with col4:
                            st.metric("Delimiter", delimiter)
                        
                        # Additional statistics
                        with st.expander("📈 Detailed Statistics"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**Column Names:**")
                                st.write(merged_df.columns.tolist())
                                
                                st.write("**Missing Values:**")
                                st.write(merged_df.isnull().sum())
                            
                            with col2:
                                st.write("**Data Types:**")
                                st.write(merged_df.dtypes.to_dict())
                                
                                st.write("**Basic Statistics:**")
                                numeric_cols = merged_df.select_dtypes(include=[np.number]).columns
                                if len(numeric_cols) > 0:
                                    st.dataframe(merged_df[numeric_cols].describe())
                    
                    # Display data preview
                    st.subheader("📊 Data Preview")
                    st.dataframe(
                        merged_df.head(10),
                        use_container_width=True,
                        height=400
                    )
                    
                    # Show all data if selected
                    if show_all_data:
                        st.subheader("📋 Complete Dataset")
                        st.dataframe(merged_df, use_container_width=True)
                        
                        # Option to download as Excel
                        if st.button("📊 Download as Excel", key="excel_download"):
                            excel_buffer = io.BytesIO()
                            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                merged_df.to_excel(writer, index=False, sheet_name='Merged_Data')
                            excel_buffer.seek(0)
                            
                            st.download_button(
                                label="📥 Click to Download Excel File",
                                data=excel_buffer,
                                file_name="Merged_EO.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    
                    # Download section
                    st.subheader("💾 Download Results")
                    
                    # CSV download
                    csv_buffer = io.StringIO()
                    merged_df.to_csv(csv_buffer, index=False)
                    csv_string = csv_buffer.getvalue()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv_string,
                            file_name=f"Merged_EO_{file_type}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        # Option to copy to clipboard
                        if st.button("📋 Copy to Clipboard", use_container_width=True):
                            st.code(csv_string[:1000] + "...", language="csv")
                            st.info("CSV data preview shown above - use Ctrl+C to copy")

if __name__ == "__main__":
    main()