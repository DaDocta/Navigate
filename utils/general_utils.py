import os
import zipfile
from lxml import etree
import pandas as pd
from tkinter import filedialog

def extract_text_from_docx(file_like_object):
    try:
        with zipfile.ZipFile(file_like_object) as docx:
            with docx.open('word/document.xml') as document_xml:
                tree = etree.parse(document_xml)
                root = tree.getroot()
                namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                texts = root.xpath('//w:t', namespaces=namespace)
                return ' '.join([text.text for text in texts if text.text])
    except Exception as e:
        print(f"Error extracting text from docx: {e}")
        return ''

def read_docx_as_xml(docx_content):
    with zipfile.ZipFile(docx_content) as docx:
        with docx.open('word/document.xml') as document_xml:
            return etree.fromstring(document_xml.read())

def search_in_word_content(fh, search_term, file_name):
    try:
        root = read_docx_as_xml(fh)
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        results = []

        current_main_item = None
        sub_items = []
        paragraphs = root.findall('.//w:p', namespaces=namespace)

        i = 0
        while i < len(paragraphs):
            paragraph = paragraphs[i]
            text = ''.join(paragraph.xpath('.//w:t/text()', namespaces=namespace)).strip()
            if not text:
                i += 1
                continue

            if search_term.lower() in text.lower():
                if current_main_item:
                    results.append((file_name, f"{current_main_item}"))
                if sub_items:
                    results.append((file_name, f"{', '.join(sub_items)}"))

                current_main_item = text
                sub_items = []

                for j in range(i + 1, len(paragraphs)):
                    sub_paragraph = paragraphs[j]
                    sub_text = ''.join(sub_paragraph.xpath('.//w:t/text()', namespaces=namespace)).strip()
                    numPr = sub_paragraph.find('.//w:numPr', namespaces=namespace)
                    if numPr is not None:
                        ilvl_elem = numPr.find('.//w:ilvl', namespaces=namespace)
                        if ilvl_elem is not None and int(ilvl_elem.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val']) > 0:
                            sub_items.append(sub_text)
                            i = j
                        else:
                            break
                    else:
                        break

            i += 1

        if current_main_item:
            if sub_items:
                results.append((file_name, f"{current_main_item}: {', '.join(sub_items)}"))
            else:
                results.append((file_name, current_main_item))

        return results

    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        return []

def search_in_excel_content(fh, search_term, file_name):
    try:
        df = pd.read_excel(fh)
        results = []
        for _, row in df.iterrows():
            row_str = ', '.join(str(cell) for cell in row)
            if search_term.lower() in row_str.lower():
                results.append((file_name, row_str))
        return results
    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        return []

def search_local_files(search_term, ai_prompt=False):
    directory = filedialog.askdirectory()
    results = []
    if not directory:
        return results

    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith('~$'):
                continue
            file_path = os.path.join(root, file)
            if file.endswith('.txt'):
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        text = f.read()
                        if search_term.lower() in text.lower():
                            results.append((file, f"Contains search term '{search_term}'"))
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
            elif file.endswith('.docx'):
                try:
                    with open(file_path, 'rb') as f:
                        docx_results = search_in_word_content(f, search_term, file)
                        results.extend(docx_results)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
            elif file.endswith('.xlsx'):
                try:
                    with open(file_path, 'rb') as f:
                        excel_results = search_in_excel_content(f, search_term, file)
                        results.extend(excel_results)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    return results
