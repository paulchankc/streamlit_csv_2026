import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class Geo_EO:
    file_path: str
    EO_filepath: str = '_EO.csv'
    ouput_filepath: str = 'Merged_EO.csv'
    def read_csv_TypeA(self):
        column_A = ['Photo Name', 'Time', 'Easting', 'Northing', 'Height', 'Omega', 'Phi', 'Kappa','M11', 'M21', 'M31','M12', 'M22','M32', 'M13', 'M23','M33']
        df = pd.read_csv(self.file_path, names=column_A, delimiter=';')
        return df
    
    def read_csv_TypeB(self):
        df = pd.read_csv(self.file_path,header=0, delimiter=';')
        df1 = df[['Image filename', 'Time', 'X1', 'Y1', 'Z1', 'Omega', 'Phi', 'Kappa','M11', 'M21', 'M31','M12', 'M22','M32', 'M13', 'M23','M33']]
        # rename the columns X1, Y1, Z1 to Easting, Northing, Height
        df1 = df1.rename(columns={'Image filename': 'Photo Name', 'X1': 'Easting', 'Y1': 'Northing', 'Z1': 'Height'})
        print(df1.head())
        return df1

    def calculate_angles(self, df):
        df['Omega'] = np.arctan2(-df['M12'],df['M11'] ) * 180 / np.pi
        df['Phi'] = -90 -np.arctan2(-df['M23'],df['M33'] ) * 180 / np.pi
        df['Kappa'] = np.arcsin(-df['M13']) * 180 / np.pi
        return df[['Photo Name', 'Omega', 'Phi', 'Kappa']]
    
    def merge_with_EO(self, angles_df):
        df2 = pd.read_csv(self.EO_filepath, header=0)
        df2 = df2[['Photo Name','Date']]
        merged_df = pd.merge( df2,angles_df, on='Photo Name')
        merged_df = merged_df[['Photo Name', 'Date','Easting', 'Northing', 'Height', 'Omega', 'Phi', 'Kappa']]
        merged_df.to_csv(self.ouput_filepath, index=False)
        return merged_df
      

if __name__ == "__main__":
    geo_eo = Geo_EO('External Orientation.csv')
    geo_eo2 = Geo_EO('External Orientation Extended.csv')
    df = geo_eo2.read_csv_TypeB()
    angles_df = geo_eo.calculate_angles(df)
    merged_df = geo_eo.merge_with_EO(angles_df)
    print(merged_df.head())


