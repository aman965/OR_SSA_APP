import streamlit as st
import os

def safe_switch_page(page_name):
    """
    Safely switch to another page in the Streamlit app
    
    Args:
        page_name (str): Name of the page to switch to (without .py extension)
    """
    try:
        st.switch_page(f"{page_name}")
    except Exception as e1:
        try:
            st.switch_page(f"pages/{page_name}")
        except Exception as e2:
            try:
                st.switch_page(f"{page_name}.py")
            except Exception as e3:
                try:
                    st.switch_page(f"pages/{page_name}.py")
                except Exception as e4:
                    st.error(f"Navigation failed: Could not switch to page {page_name}")
                    st.error(f"Errors: {str(e1)}, {str(e2)}, {str(e3)}, {str(e4)}")

def get_page_url(page_name):
    """
    Get the URL for a page in the Streamlit app
    
    Args:
        page_name (str): Name of the page (without .py extension)
        
    Returns:
        str: HTML for a link to the page
    """
    return f'<a href="/{page_name}" target="_self">Go to {page_name}</a>'

def navigation_button(label, page_name, use_container_width=False):
    """
    Create a navigation button that safely switches to another page
    
    Args:
        label (str): Button label
        page_name (str): Name of the page to navigate to (without .py extension)
        use_container_width (bool): Whether to use the full container width
    """
    if st.button(label, use_container_width=use_container_width):
        safe_switch_page(page_name)
        
def navigation_fallback(page_name):
    """
    Provide HTML fallback navigation in case st.switch_page fails
    
    Args:
        page_name (str): Name of the page to navigate to (without .py extension)
    """
    st.markdown(
        f'<p>If automatic navigation fails, <a href="/{page_name}" target="_self">click here</a> to go to {page_name}.</p>',
        unsafe_allow_html=True
    )
