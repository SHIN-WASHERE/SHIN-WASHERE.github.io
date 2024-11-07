import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io 
from datetime import datetime

# ตั้งค่าหน้าเพจ
st.set_page_config(page_title="License Monitor", layout="wide")
st.title("ระบบ tracking การอบรมหลักสูตร SAFETY")

st.markdown("""
    <style>
    .stDownloadButton > button {
        background-color: #ff5c5c;  /* สีพื้นหลังปุ่ม */
        color: white;  /* สีตัวอักษร */
        border-radius: 8px;  /* ปรับขอบปุ่มให้นุ่มนวล */
        border: none; /* เอาเส้นขอบออก */
    }
    .stDownloadButton > button:hover {
        background-color: #000000;  /* สีปุ่มเมื่อเอาเมาส์ไปวาง */
        color: #ffffff;  /* สีตัวอักษรเมื่อเอาเมาส์ไปวาง */
    }
    </style>
""", unsafe_allow_html=True)

# อัพโหลดไฟล์
file = st.file_uploader("อัพโหลดไฟล์ Excel", type=['xlsx'])

if file:
    try:
        # อ่านข้อมูล
        df = pd.read_excel(file)
        
        # แสดงข้อมูลต้นฉบับ
        st.subheader("ข้อมูลดิบ")
        st.dataframe(df)
        
        # คำนวณวันหมดอายุ
        if 'license_expire_date' in df.columns:
            df['license_expire_date'] = pd.to_datetime(df['license_expire_date'], errors='coerce')
            df['days_until_expire'] = (df['license_expire_date'] - datetime.now()).dt.days
            
            # จัดกลุ่มสถานะ
            conditions = [
                (df['days_until_expire'] <= 0),
                (df['days_until_expire'] <= 30),
                (df['days_until_expire'] <= 90),
                (df['days_until_expire'] > 90)
            ]
            choices = ['หมดอายุ', 'ใกล้หมดอายุ (30 วัน)', 'ต้องต่ออายุเร็วๆนี้', 'ปกติ']
            df['status'] = np.select(conditions, choices, default='ไม่ระบุ')
            
            # แสดงสถิติ
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ทั้งหมด", len(df))
            with col2:
                st.metric("หมดอายุ", len(df[df['status'] == 'หมดอายุ']))
            with col3:
                st.metric("ใกล้หมดอายุ", len(df[df['status'] == 'ใกล้หมดอายุ (30 วัน)']))
            with col4:
                st.metric("ปกติ", len(df[df['status'] == 'ปกติ']))
            
            # แสดงกราฟวงกลม
            status_counts = df['status'].value_counts()
            fig = px.pie(values=status_counts.values, 
                        names=status_counts.index, 
                        title='สัดส่วนสถานะใบประกอบวิชาชีพ')
            st.plotly_chart(fig)
            
            # เพิ่มตัวกรองคณะ, โปรแกรม และสถานะ
            if 'faculty' in df.columns and 'program' in df.columns:
                col1, col2, col3 = st.columns(3)
                with col1:
                    selected_faculty = st.multiselect(
                        "เลือกคณะ",
                        options=df['faculty'].unique(),
                        default=df['faculty'].unique()
                    )
                with col2:
                    selected_program = st.multiselect(
                        "เลือกโปรแกรม",
                        options=df['program'].unique(),
                        default=df['program'].unique()
                    )
                with col3:
                    selected_status = st.multiselect(
                        "เลือกสถานะ",
                        options=['หมดอายุ', 'ใกล้หมดอายุ (30 วัน)', 'ต้องต่ออายุเร็วๆนี้', 'ปกติ'],
                        default=['หมดอายุ', 'ใกล้หมดอายุ (30 วัน)']
                    )
                
                # กรองข้อมูล
                filtered_df = df[
                    (df['faculty'].isin(selected_faculty)) &
                    (df['program'].isin(selected_program)) &
                    (df['status'].isin(selected_status))
                ]
                
                # แสดงรายชื่อที่ต้องติดตาม
                st.subheader("รายชื่อที่ต้องติดตาม")
                if not filtered_df.empty:
                    # จัดเรียงตามวันที่ใกล้หมดอายุ
                    filtered_df = filtered_df.sort_values('days_until_expire')
                    st.dataframe(filtered_df[[
                        'student_id', 'full_name', 'license_number',
                        'license_expire_date', 'phone', 'email',
                        'faculty', 'program', 'status'
                    ]])
                    
                    output = io.BytesIO()
                    filtered_df.to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)  
                    st.download_button(
                        label=" 😭 ดาวน์โหลดรายงาน",
                        data=output,
                        file_name="follow_up_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )   
                else:
                    st.info("ไม่พบข้อมูลที่ต้องติดตาม")
            else:
                st.warning("ไม่พบคอลัมน์ 'faculty' หรือ 'program' ในไฟล์ Excel")
        else:
            st.error("ไม่พบคอลัมน์ 'license_expire_date' ในไฟล์ Excel")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {str(e)}")
        st.write("กรุณาตรวจสอบรูปแบบไฟล์และข้อมูลของคุณ")
