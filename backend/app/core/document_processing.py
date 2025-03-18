import os
import fitz  # PyMuPDF
import langdetect
from typing import Dict, Any, List, Optional

class DocumentProcessor:
    """
    Handles the processing of various document types, extracting text, metadata,
    tables, and images from different file formats.
    """
    
    @staticmethod
    def format_pdf_date(date_string: str) -> str:
        """
        Format PDF date string (format D:YYYYMMDDHHmmSSOHH'mm') to a readable date format.
        
        Args:
            date_string: PDF date string in format D:YYYYMMDDHHmmSSOHH'mm'
            
        Returns:
            Formatted date string in YYYY-MM-DD HH:MM:SS format
        """
        try:
            if not date_string or not isinstance(date_string, str):
                return ""
                
            # Remove 'D:' prefix if present
            if date_string.startswith('D:'):
                date_string = date_string[2:]
                
            # Extract basic components
            if len(date_string) >= 14:
                year = date_string[0:4]
                month = date_string[4:6]
                day = date_string[6:8]
                hour = date_string[8:10]
                minute = date_string[10:12]
                second = date_string[12:14]
                
                return f"{year}-{month}-{day} {hour}:{minute}:{second}"
            else:
                return date_string  # Return as is if format not recognized
        except Exception as e:
            print(f"Error formatting PDF date: {str(e)}")
            return date_string  # Return original on error
    
    @staticmethod
    async def process_page(page) -> Dict[str, Any]:
        """
        Process a single page from a PDF document.
        
        Args:
            page: A PyMuPDF page object
        
        Returns:
            Dict with page content, tables, images, and other extracted information
        """
        try:
            # Extract text from the page
            text = page.get_text()
            
            # Initialize empty collections for tables and blocks
            tables = []
            blocks = []
            images = []
            
            # Get page blocks (structured content)
            try:
                # Extract blocks from the page - using the appropriate PyMuPDF methods
                for block in page.get_text("dict")["blocks"]:
                    if block["type"] == 0:  # Text block
                        blocks.append({
                            "type": "text",
                            "bbox": block["bbox"],
                            "text": block.get("text", ""),
                            "font": "",  # Not always available in this format
                            "size": 0     # Not always available in this format
                        })
                    elif block["type"] == 1:  # Image block
                        blocks.append({
                            "type": "image",
                            "bbox": block["bbox"],
                            "text": "",
                            "font": "",
                            "size": 0
                        })
            except Exception as e:
                print(f"Error extracting blocks: {str(e)}")
            
            # Extract images if available
            try:
                image_list = page.get_images(full=True)
                for img_idx, img_info in enumerate(image_list):
                    try:
                        xref = img_info[0]  # Cross-reference number
                        base_image = page.parent.extract_image(xref)
                        if base_image:
                            image_data = {
                                "index": img_idx,
                                "width": base_image.get("width", 0),
                                "height": base_image.get("height", 0),
                                "format": base_image.get("ext", ""),
                                "data": None  # Not storing binary data here
                            }
                            images.append(image_data)
                    except Exception as img_err:
                        print(f"Error extracting image {img_idx}: {str(img_err)}")
            except Exception as e:
                print(f"Error processing images: {str(e)}")
            
            # For tables, we would need a table detection algorithm
            # This is a simplified approach - looking for content that might be tables
            # based on layout and structure
            try:
                # A simple heuristic for detecting potential tables
                # This is a placeholder and not a real table detection
                potential_tables = []
                
                # In a real implementation, we would use a more sophisticated 
                # table detection algorithm here
                
                # For now, just add dummy example
                if len(text) > 200 and '|' in text:
                    # Simple heuristic: text contains pipe characters might be a table
                    lines = [line for line in text.split('\n') if '|' in line]
                    if len(lines) > 2:  # At least a header and one data row
                        table_data = []
                        for line in lines:
                            row = [cell.strip() for cell in line.split('|')]
                            table_data.append(row)
                        tables.append(table_data)
            except Exception as e:
                print(f"Error detecting tables: {str(e)}")
            
            # Return the extracted information
            return {
                "text": text,
                "tables": tables,
                "images": images,
                "blocks": blocks
            }
        except Exception as e:
            print(f"Error processing page: {str(e)}")
            return {
                "text": "",
                "tables": [],
                "images": [],
                "blocks": []
            }
    
    @staticmethod
    async def extract_pdf_metadata(pdf_document) -> Dict[str, Any]:
        """
        Extract metadata from a PDF document.
        
        Args:
            pdf_document: A PyMuPDF document object
            
        Returns:
            Dictionary containing metadata fields
        """
        metadata = {
            "title": "",
            "author": "",
            "subject": "",
            "keywords": "",
            "creation_date": "",
            "modified_date": "",
            "page_count": 0,
            "file_type": "pdf"
        }
        
        try:
            # Set page count
            metadata["page_count"] = len(pdf_document)
            
            if hasattr(pdf_document, 'metadata') and pdf_document.metadata:
                pdf_meta = pdf_document.metadata
                if isinstance(pdf_meta, dict):
                    # Dictionary access
                    metadata["title"] = pdf_meta.get("title", "")
                    metadata["author"] = pdf_meta.get("author", "")
                    metadata["subject"] = pdf_meta.get("subject", "")
                    metadata["keywords"] = pdf_meta.get("keywords", "")
                    
                    if pdf_meta.get("creationDate"):
                        metadata["creation_date"] = DocumentProcessor.format_pdf_date(pdf_meta.get("creationDate"))
                        
                    if pdf_meta.get("modDate"):
                        metadata["modified_date"] = DocumentProcessor.format_pdf_date(pdf_meta.get("modDate"))
                        
                elif hasattr(pdf_meta, 'title'):
                    # Object attribute access
                    metadata["title"] = getattr(pdf_meta, 'title', "")
                    metadata["author"] = getattr(pdf_meta, 'author', "")
                    metadata["subject"] = getattr(pdf_meta, 'subject', "")
                    metadata["keywords"] = getattr(pdf_meta, 'keywords', "")
                    
                    if hasattr(pdf_meta, 'creation_date'):
                        metadata["creation_date"] = DocumentProcessor.format_pdf_date(getattr(pdf_meta, 'creation_date', ""))
                        
                    if hasattr(pdf_meta, 'mod_date'):
                        metadata["modified_date"] = DocumentProcessor.format_pdf_date(getattr(pdf_meta, 'mod_date', ""))
        except Exception as e:
            print(f"Error extracting PDF metadata: {str(e)}")
            
        return metadata
    
    @staticmethod
    async def process_pdf(file_path: str) -> Dict[str, Any]:
        """
        Process a PDF document, extracting text, metadata, and structure.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing the processed PDF data
        """
        result = {
            "content": "",
            "pages": [],
            "metadata": {
                "title": os.path.basename(file_path),
                "page_count": 0,
                "file_type": "pdf"
            },
            "tables": [],
            "images": [],
            "language": "en",
            "entities": [],
            "summary": ""
        }
        
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(file_path)
            
            # Extract metadata
            result["metadata"] = await DocumentProcessor.extract_pdf_metadata(pdf_document)
            
            # Process each page
            full_text = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_content = await DocumentProcessor.process_page(page)
                
                # Add page text to full document text
                if page_content.get("text"):
                    full_text += page_content["text"] + "\n\n"
                
                # Add page to results
                result["pages"].append({
                    "number": page_num + 1,
                    "content": page_content
                })
                
                # Collect tables from all pages
                for table in page_content.get("tables", []):
                    result["tables"].append({
                        "page": page_num + 1,
                        **table
                    })
                
                # Collect images from all pages
                for image in page_content.get("images", []):
                    result["images"].append({
                        "page": page_num + 1,
                        **image
                    })
            
            # Store the full text
            result["content"] = full_text.strip()
            
            # Detect language if text available
            if full_text.strip():
                try:
                    result["language"] = langdetect.detect(full_text)
                except Exception as e:
                    print(f"Language detection error: {str(e)}")
                    result["language"] = "en"  # Default to English
            
            # Close the PDF document
            pdf_document.close()
            
        except Exception as e:
            print(f"Error processing PDF file: {str(e)}")
            result["content"] = f"Error processing PDF: {str(e)}"
            result["summary"] = f"Failed to process PDF: {str(e)}"
        
        return result
    
    @staticmethod
    async def process_document(file_path: str) -> Dict[str, Any]:
        """
        Process a document, identifying its type and using the appropriate processor.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing processed document data
        """
        # Initialize default result structure
        result = {
            "content": "",
            "pages": [],
            "metadata": {
                "title": os.path.basename(file_path),
                "page_count": 0,
                "file_type": "unknown"
            },
            "tables": [],
            "images": [],
            "language": "en",
            "entities": [],
            "summary": ""
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result["content"] = f"File not found: {file_path}"
                return result
            
            # Determine file type from extension
            file_extension = os.path.splitext(file_path)[1].lower()[1:]
            result["metadata"]["file_type"] = file_extension
            
            # Process based on file type
            if file_extension == "pdf":
                return await DocumentProcessor.process_pdf(file_path)
            else:
                # For other document types (placeholder for future implementation)
                try:
                    with open(file_path, 'rb') as f:
                        content = f"Content extracted from {file_extension} file. Full processing not implemented."
                    result["content"] = content
                    result["pages"].append({
                        "number": 1,
                        "content": {
                            "text": content,
                            "tables": [],
                            "images": [],
                            "blocks": []
                        }
                    })
                    result["metadata"]["page_count"] = 1
                except Exception as e:
                    print(f"Error reading {file_extension} file: {str(e)}")
                    result["content"] = f"Error reading file: {str(e)}"
                    result["summary"] = f"Document processing failed: {str(e)}"
        except Exception as e:
            print(f"Critical error in document processing: {str(e)}")
            result["content"] = f"Error processing document: {str(e)}"
            result["summary"] = f"Document processing failed: {str(e)}"
        
        return result
