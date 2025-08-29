import streamlit as st
import requests
import json
import pandas as pd

# إعداد الصفحة
st.set_page_config(
    page_title="Course Folders Browser",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Course Folders Browser")
st.markdown("---")

# تهيئة session state
if 'folders_data' not in st.session_state:
    st.session_state.folders_data = None
if 'expanded_folders' not in st.session_state:
    st.session_state.expanded_folders = set()

def get_inputs():
    """Helper function to get and parse inputs from the Streamlit form."""
    full_url = st.session_state.course_url
    try:
        base_url, course_id = full_url.rsplit('/', 1)
        if not course_id.isdigit():
            raise ValueError("Course ID must be a number.")
    except ValueError as e:
        st.error(f"Invalid Course URL format. {e}")
        return None, None, None

    try:
        headers = json.loads(st.session_state.headers_json)
    except json.JSONDecodeError:
        st.error("Invalid JSON format in headers.")
        return None, None, None
    
    return base_url, course_id, headers

def fetch_folders():
    """Fetch folders from the API and store in session state."""
    base_url, course_id, headers = get_inputs()
    if not all((base_url, course_id, headers)):
        return False

    try:
        with st.spinner("جاري تحميل المجلدات..."):
            # جلب بيانات الكورس
            course_response = requests.get(f"{base_url}/{course_id}", headers=headers)
            
            # التحقق من حالة الاستجابة
            if course_response.status_code != 200:
                st.error(f"خطأ في الاستجابة: {course_response.status_code}")
                st.json(course_response.text)
                return False
            
            course_data = course_response.json()
            
            # طباعة البيانات لفهم البنية
            st.write("**بنية البيانات المُستلمة:**")
            st.json(course_data)
            
            # محاولة الوصول للمجلدات مع معالجة أفضل للأخطاء
            if "data" in course_data:
                if "folders" in course_data["data"]:
                    folders = course_data["data"]["folders"]
                else:
                    st.error("لم يتم العثور على 'folders' في 'data'")
                    st.write("المفاتيح المتاحة في 'data':", list(course_data["data"].keys()))
                    return False
            else:
                st.error("لم يتم العثور على 'data' في الاستجابة")
                st.write("المفاتيح المتاحة:", list(course_data.keys()))
                return False
            
            folders_data = []
            
            for folder in folders:
                try:
                    folder_id = folder.get("id")
                    if not folder_id:
                        st.warning(f"مجلد بدون ID: {folder}")
                        continue
                        
                    # جلب تفاصيل المجلد
                    folder_response = requests.get(f"{base_url}/folders/{folder_id}", headers=headers)
                    
                    if folder_response.status_code != 200:
                        st.warning(f"خطأ في جلب المجلد {folder_id}: {folder_response.status_code}")
                        continue
                        
                    folder_details_response = folder_response.json()
                    
                    # التحقق من بنية بيانات المجلد
                    if "data" not in folder_details_response:
                        st.warning(f"بيانات المجلد {folder_id} لا تحتوي على 'data'")
                        continue
                        
                    folder_details = folder_details_response["data"]
                    
                    folder_info = {
                        'id': folder_id,
                        'name': folder_details.get("name", f"مجلد {folder_id}"),
                        'type': 'Folder',
                        'children': []
                    }
                    
                    # معالجة المجلدات الفرعية
                    children = folder_details.get("children", [])
                    for child in children:
                        child_info = {
                            'name': child.get("name", "مجلد فرعي"),
                            'type': 'Subfolder',
                            'materials': []
                        }
                        
                        # معالجة المواد
                        materials = child.get("materials", [])
                        for material in materials:
                            try:
                                materialable = material.get("materialable", {})
                                link = materialable.get("link", "")
                                
                                if link:
                                    material_info = {
                                        'name': material.get("name", "ملف غير معنون"),
                                        'link': link,
                                        'type': 'File'
                                    }
                                    child_info['materials'].append(material_info)
                            except Exception as material_error:
                                st.warning(f"خطأ في معالجة المادة: {material_error}")
                                continue
                        
                        folder_info['children'].append(child_info)
                    
                    folders_data.append(folder_info)
                    
                except Exception as folder_error:
                    st.warning(f"خطأ في معالجة المجلد {folder.get('id', 'unknown')}: {folder_error}")
                    continue
            
            if folders_data:
                st.session_state.folders_data = folders_data
                st.success(f"تم تحميل {len(folders_data)} مجلد بنجاح!")
                return True
            else:
                st.warning("لم يتم العثور على مجلدات صالحة")
                return False
            
    except requests.RequestException as e:
        st.error(f"خطأ في الاتصال بالشبكة: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        st.error(f"خطأ في تحليل JSON: {str(e)}")
        return False
    except Exception as e:
        st.error(f"خطأ غير متوقع: {str(e)}")
        return False

def generate_curl_command(link, filename, headers):
    """Generate curl command for downloading a file."""
    curl_cmd = f'''curl -L "{link}" \\
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
    
    return curl_cmd

def display_folders():
    """Display folders in an expandable format."""
    if not st.session_state.folders_data:
        st.info("قم بتحميل المجلدات أولاً")
        return
    
    st.markdown("## 📁 المجلدات والملفات")
    
    for folder in st.session_state.folders_data:
        with st.expander(f"📁 {folder['name']}", expanded=False):
            if not folder['children']:
                st.write("لا توجد مجلدات فرعية")
                continue
                
            for child in folder['children']:
                st.markdown(f"### 📂 {child['name']}")
                
                if not child['materials']:
                    st.write("لا توجد ملفات")
                    continue
                
                # إنشاء DataFrame للملفات
                files_data = []
                for material in child['materials']:
                    files_data.append({
                        'الملف': material['name'],
                        'الرابط': material['link']
                    })
                
                if files_data:
                    df = pd.DataFrame(files_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # أزرار التحميل لكل ملف
                    for i, material in enumerate(child['materials']):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📄 {material['name']}")
                        with col2:
                            if st.button(f"📥 تحميل", key=f"download_{folder['id']}_{i}"):
                                show_download_dialog(material['name'], material['link'])

def show_download_dialog(filename, link):
    """Show download dialog with curl command."""
    _, _, headers = get_inputs()
    if not headers:
        return
    
    curl_cmd = generate_curl_command(link, filename, headers)
    
    st.markdown("### 💾 أمر التحميل")
    st.code(curl_cmd, language="bash")
    
    # مسارات النسخ
    destination_folder = "/storage/emulated/0/كورس/"
    destination_contents = destination_folder + "*"
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 نسخ أمر curl"):
            st.write("تم نسخ الأمر! (استخدم Ctrl+C لنسخه يدوياً)")
    
    with col2:
        if st.button("📁 نسخ مسار الوجهة"):
            st.code(destination_contents)
            st.write("مسار محتويات الوجهة")

# واجهة المستخدم الرئيسية
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### ⚙️ الإعدادات")
    
    # Course URL
    course_url = st.text_input(
        "Course URL:",
        value="https://em.wefaq.site/api/student/enrollments/courses/2495",
        key="course_url"
    )
    
    # Headers
    st.markdown("**Headers (JSON):**")
    initial_headers = {
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
        "Headers JSON:",
        value=json.dumps(initial_headers, indent=2),
        height=300,
        key="headers_json"
    )
    
    # زر تحميل المجلدات
    if st.button("🔄 عرض المجلدات", type="primary"):
        fetch_folders()

with col2:
    st.markdown("### 📚 عرض المجلدات")
    display_folders()

# معلومات إضافية في الشريط الجانبي
with st.sidebar:
    st.markdown("### 📋 معلومات التطبيق")
    st.markdown("""
    - **الغرض**: تصفح مجلدات الدورة وتحميل الملفات
    - **الطريقة**: استخدام أوامر curl لتحميل الملفات
    - **المتطلبات**: صالحية headers للوصول للـ API
    """)
    
    if st.session_state.folders_data:
        total_folders = len(st.session_state.folders_data)
        total_files = sum(
            len(child['materials']) 
            for folder in st.session_state.folders_data 
            for child in folder['children']
        )
        
        st.metric("عدد المجلدات", total_folders)
        st.metric("عدد الملفات", total_files)
    
    st.markdown("---")
    st.markdown("### 🛠️ كيفية الاستخدام")
    st.markdown("""
    1. تأكد من صحة Course URL
    2. تأكد من صحة Headers JSON
    3. اضغط على "عرض المجلدات"
    4. اختر الملف المراد تحميله
    5. انسخ أمر curl وشغله في الطرفية
    """)
