import os
import streamlit as st
from rag_pipeline import configure, fact_check, FactCheckResult

# File type detection function
def get_file_type(file):
    file_name = file.name
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
        return 'audio'
    elif file_extension in ['.mp4', '.avi', '.mov', '.mkv', '.flv']:
        return 'video' 
    elif file_extension in ['.txt', '.doc', '.docx', '.pdf', '.rtf']:
        return 'text'
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
        return 'images'
    else:
        return None

def display_factcheck(result: FactCheckResult):
    """Enhanced display of fact-check results"""
    st.subheader("🔍 Fact-Checking Results")
    
    # Trust score with color coding
    score_color = (
        "red" if result.trust_score < 40 
        else "orange" if result.trust_score < 70 
        else "green"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.metric("Trust Score", f"{result.trust_score:.0f}/100")
    with col2:
        st.markdown(
            f"<span style='color:{score_color}; font-size:24px'>■</span> "
            f"<span style='vertical-align:middle'>Confidence Level</span>",
            unsafe_allow_html=True
        )
    
    # Explanation
    st.markdown("### 📝 Explanation")
    st.info(result.explanation)
    
    # Supporting points
    if result.supporting_points:
        st.markdown("### ✅ Supporting Evidence")
        for point in result.supporting_points:
            st.markdown(f"- {point}")
    
    # Contradictory points
    if result.contradictory_points:
        st.markdown("### ❌ Contradictory Evidence")
        for point in result.contradictory_points:
            st.markdown(f"- {point}")
    
    # Raw evidence expander
    with st.expander("🔍 View raw evidence sources"):
        st.text(result.raw_evidence[:10000] + ("..." if len(result.raw_evidence) > 10000 else ""))

def main():
    st.set_page_config(
        page_title="Multimodal Fact Checker", 
        page_icon="🔍",
        layout="wide"
    )
    st.title("📄 Multimodal File Summarizer with Fact-Checking")
    
    # Initialize APIs
    if not configure():
        st.error("Failed to configure API connections. Please check your keys and internet connection.")
        st.stop()
    
    uploaded_file = st.file_uploader(
        "Upload your file", 
        type=["mp3", "wav", "mp4", "avi", "txt", "pdf", "jpg", "png", "docx"],
        help="Supported formats: Audio (MP3, WAV), Video (MP4, AVI), Text (TXT, PDF, DOCX), Images (JPG, PNG)"
    )

    if uploaded_file is not None:
        file_format = get_file_type(uploaded_file)
        st.write(f"🔹 Detected file type: **{file_format.capitalize()}**")

        # Generate summary
        summary = ""
        try:
            if file_format == 'audio':
                import audio
                summary = audio.summarize_audio(uploaded_file)
            elif file_format == 'video':
                import video
                summary = video.summarize_video(uploaded_file)
            elif file_format == 'text':
                import text
                summary = text.summarize_text(uploaded_file)
            elif file_format == 'images':
                import images
                summary = images.summarize_image(uploaded_file)
            else:
                summary = "Unsupported file type."
        except Exception as e:
            st.error(f"❌ Error generating summary: {str(e)}")
            st.stop()

        if summary and "Unsupported" not in summary:
            st.subheader("📝 Summary:")
            st.write(summary)

            # Fact-checking section
            st.divider()
            st.subheader("🔎 Fact-Checking Analysis")
            
            with st.spinner("🔍 Retrieving evidence and analyzing..."):
                try:
                    result = fact_check(summary)
                    display_factcheck(result)
                except Exception as e:
                    st.error(f"❌ Fact-checking failed: {str(e)}")

if __name__ == "__main__":
    main()