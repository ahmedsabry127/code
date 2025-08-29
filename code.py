import streamlit as st
import requests
import json
from typing import Optional, Tuple, Dict, Any

# تكوين الصفحة
st.set_page_config(
    page_title="Course Folders Browser",
    page_icon="📚",
    layout="wide"
)

# CSS مخصص لتحسين المظهر
st.markdown("""
<style>
.stTextArea textarea {
    font-family: 'Courier New', monospace;
    font-size: 12px;
}
.download-command {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 5px;
    border-left: 4px solid #4CAF50;
    margin: 10px 0;
}
.file-item {
    background-color: #ffffff;
    padding: 8px;
    border-radius: 4px;
    border: 1px solid #e0e0e0;
    margin: 4px 0;
}
.folder-item {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

def get_parsed_inputs(course_url: str, headers_json: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
    """تحليل المدخلات والتحقق من صحتها."""
    try:
        # تحليل URL
        if not course_url.strip():
            st.error("يرجى إدخال رابط الكورس")
            return None
        
        base_url, course_id = course_url.rsplit('/', 1)
        if not course_id.isdigit():
            st.error("معرف الكورس يجب أن يكون رقمًا")
            return None
        
        # تحليل Headers
        headers = json.loads(headers_json)
        return base_url, course_id, headers
    
    except ValueError as e:
        st.error(f"خطأ في تنسيق رابط الكورس: {e}")
        return None
    except json.JSONDecodeError:
        st.error("خطأ في تنسيق JSON للـ headers")
        return None

@st.cache_data(ttl=300)  # Cache لمدة 5 دقائق
def fetch_course_data(base_url: str, course_id: str, headers: Dict[str, Any]):
    """جلب بيانات الكورس والمجلدات."""
    try:
        # جلب بيانات الكورس
        course_response = requests.get(f"{base_url}/{course_id}", headers=headers, timeout=30)
        course_response.raise_for_status()
        course = course_response.json()
        
        if "data" not in course or "folders" not in course["data"]:
            st.error("لم يتم العثور على مجلدات في الكورس")
            return None
        
        folders = course["data"]["folders"]
        
        # جلب تفاصيل كل مجلد
        detailed_folders = []
        progress_bar = st.progress(0)
        total_folders = len(folders)
        
        for i, folder in enumerate(folders):
            folder_id = folder["id"]
            try:
                folder_response = requests.get(
                    f"{base_url}/folders/{folder_id}", 
                    headers=headers, 
                    timeout=30
                )
                folder_response.raise_for_status()
                folder_details = folder_response.json()["data"]
                detailed_folders.append(folder_details)
            except Exception as e:
                st.warning(f"تعذر جلب المجلد {folder.get('name', 'غير معروف')}: {e}")
            
            progress_bar.progress((i + 1) / total_folders)
        
        progress_bar.empty()
        return detailed_folders
        
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في الشبكة: {e}")
        return None
    except Exception as e:
        st.error(f"خطأ غير متوقع: {e}")
        return None

def generate_curl_command(link: str, filename: str, headers: Dict[str, Any]) -> str:
    """إنشاء أمر curl للتنزيل."""
    return f'''curl -L "{link}" \\
  -H "lang: {headers.get('lang', 'en')}" \\
  -H "x-secret: {headers.get('x-secret', '')}" \\
  -H "authorization: {headers.get('authorization', '')}" \\
  -H "x-device-token: {headers.get('x-device-token', '')}" \\
  -H "x-app-version: {headers.get('x-app-version', '')}" \\
  -H "x-device-type: {headers.get('x-device-type', '')}" \\
  -H "x-device-version: {headers.get('x-device-version', '')}" \\
  -H "accept-encoding: {headers.get('accept-encoding', 'gzip')}" \\
  -H "user-agent: {headers.get('user-agent', '')}" \\
  -o "/storage/emulated/0/كورس/{filename}"'''

def main():
    st.title("📚 Course Folders Browser")
    st.markdown("تطبيق لتصفح مجلدات الكورسات وإنشاء أوامر التنزيل")
    
    # شريط جانبي للإعدادات
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        
        # رابط الكورس
        course_url = st.text_input(
            "رابط الكورس:",
            value="https://em.wefaq.site/api/student/enrollments/courses/2495",
            help="أدخل الرابط الكامل للكورس"
        )
        
        # Headers
        st.subheader("Headers (JSON)")
        default_headers = {
            "lang": "en",
            "x-secret": "ANDROIDVwwLSXBsib2Ytwca30042025",
            "authorization": "Bearer 56248|RKNE6szV5Tw9L7EtkZtVx4kLM98kR0Q8TiLZWa4j840a9dd1",
            "x-device-token": "e593febbfcc5ff78",
            "x-app-version": "1.43",
            "x-device-type": "android",
            "x-device-version": "samsung, Android 15, SM-X510",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.11.0"
        }
        
        headers_json = st.text_area(
            "Headers:",
            value=json.dumps(default_headers, indent=2),
            height=300,
            help="أدخل الـ headers بصيغة JSON"
        )
        
        # زر جلب البيانات
        fetch_button = st.button("🔄 جلب المجلدات", type="primary")
    
    # المحتوى الرئيسي
    if fetch_button:
        parsed_data = get_parsed_inputs(course_url, headers_json)
        if parsed_data:
            base_url, course_id, headers = parsed_data
            
            with st.spinner("جاري جلب بيانات الكورس..."):
                folders_data = fetch_course_data(base_url, course_id, headers)
            
            if folders_data:
                st.session_state['folders_data'] = folders_data
                st.session_state['headers'] = headers
                st.success(f"تم جلب {len(folders_data)} مجلد بنجاح!")
    
    # عرض المجلدات المحفوظة
    if 'folders_data' in st.session_state and st.session_state['folders_data']:
        st.header("📁 المجلدات والملفات")
        
        folders_data = st.session_state['folders_data']
        headers = st.session_state['headers']
        
        # فلتر البحث
        search_term = st.text_input("🔍 البحث في الملفات:", placeholder="اكتب اسم الملف...")
        
        for folder in folders_data:
            with st.expander(f"📁 {folder.get('name', 'مجلد غير معروف')}", expanded=False):
                
                children = folder.get("children", [])
                if not children:
                    st.info("لا توجد مجلدات فرعية")
                    continue
                
                for child in children:
                    st.markdown(f"**📂 {child.get('name', 'مجلد فرعي')}**")
                    
                    materials = child.get("materials", [])
                    if not materials:
                        st.info("لا توجد ملفات في هذا المجلد")
                        continue
                    
                    # فلترة الملفات حسب البحث
                    filtered_materials = materials
                    if search_term:
                        filtered_materials = [
                            m for m in materials 
                            if search_term.lower() in m.get("name", "").lower()
                        ]
                    
                    if not filtered_materials:
                        st.info("لا توجد ملفات مطابقة للبحث")
                        continue
                    
                    for idx, material in enumerate(filtered_materials):
                        material_name = material.get("name", "ملف غير معروف")
                        materialable = material.get("materialable", {})
                        link = materialable.get("link", "")
                        
                        if not link:
                            st.warning(f"⚠️ {material_name} - لا يوجد رابط")
                            continue
                        
                        # عرض معلومات الملف
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"📄 **{material_name}**")
                            st.caption(f"الرابط: {link[:50]}..." if len(link) > 50 else link)
                        
                        with col2:
                            # زر لإنشاء أمر curl
                            if st.button(f"💻 أمر التنزيل", key=f"curl_{folder['name']}_{child['name']}_{idx}"):
                                curl_command = generate_curl_command(link, material_name, headers)
                                
                                # عرض الأمر في modal
                                st.subheader(f"أمر تنزيل: {material_name}")
                                st.code(curl_command, language="bash")
                                
                                # أزرار النسخ
                                col_a, col_b, col_c = st.columns(3)
                                
                                with col_a:
                                    if st.button("📋 نسخ الأمر", key=f"copy_curl_{idx}"):
                                        st.write("```bash")
                                        st.write(curl_command)
                                        st.write("```")
                                        st.success("تم عرض الأمر - يمكنك نسخه من الأعلى")
                                
                                with col_b:
                                    destination_path = f"/storage/emulated/0/كورس/{material_name}"
                                    if st.button("📂 نسخ المسار", key=f"copy_path_{idx}"):
                                        st.code(destination_path)
                                        st.success("تم عرض المسار - يمكنك نسخه من الأعلى")
                                
                                with col_c:
                                    folder_contents = "/storage/emulated/0/كورس/*"
                                    if st.button("📁 محتويات المجلد", key=f"copy_contents_{idx}"):
                                        st.code(folder_contents)
                                        st.success("تم عرض مسار المحتويات")
                        
                        st.divider()
    
    # معلومات إضافية
    with st.sidebar:
        st.markdown("---")
        st.subheader("ℹ️ معلومات")
        st.info("""
        هذا التطبيق يساعدك في:
        - تصفح مجلدات الكورسات
        - إنشاء أوامر curl للتنزيل
        - البحث في الملفات
        - نسخ المسارات والأوامر
        """)
        
        if st.button("🗑️ مسح البيانات المحفوظة"):
            for key in ['folders_data', 'headers']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("تم مسح البيانات")
            st.experimental_rerun()

if __name__ == "__main__":
    main()
