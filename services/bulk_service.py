import io
import re
import zipfile
from typing import Dict, Any, List, Optional
import pandas as pd
from PIL import Image
from services.qr_service import generate_qr_image


def parse_uploaded_dataset(file_obj, filename: str) -> pd.DataFrame:
    """Reads uploaded CSV or Excel file into a Pandas DataFrame."""
    if filename.endswith(".csv"):
        df = pd.read_csv(file_obj)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_obj)
    else:
        raise ValueError("Unsupported file format. Please upload a .csv or .xlsx file.")
    return df


def sanitize_filename(name: str) -> str:
    """Sanitizes text to safe filenames."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name.strip())
    clean = re.sub(r"\s+", "_", clean)
    return clean[:50] or "qr_code"


def generate_bulk_qrs(
    df: pd.DataFrame,
    content_col: str,
    name_col: Optional[str] = None,
    fill_color: str = "#8B5CF6",
    back_color: str = "#FFFFFF",
    size: int = 256,
) -> Dict[str, Any]:
    """
    Generates QR codes in bulk from a DataFrame and compiles them into a ZIP archive.
    """
    zip_buffer = io.BytesIO()
    results: List[Dict[str, Any]] = []
    generated_count = 0
    skipped_count = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, (_, row) in enumerate(df.iterrows(), start=1):
            raw_content = row.get(content_col)

            # Skip empty records
            if pd.isna(raw_content) or not str(raw_content).strip():
                skipped_count += 1
                continue

            content_str = str(raw_content).strip()

            if name_col and name_col in df.columns and not pd.isna(row.get(name_col)):
                base_name = sanitize_filename(str(row[name_col]))
            else:
                base_name = f"qr_{idx}"

            filename = f"{base_name}_{idx}.png"

            try:
                img: Image.Image = generate_qr_image(
                    payload=content_str,
                    fill_color=fill_color,
                    back_color=back_color,
                    size=size,
                )
                img_bytes_buf = io.BytesIO()
                img.save(img_bytes_buf, format="PNG")
                png_bytes = img_bytes_buf.getvalue()

                # Add to ZIP
                zip_file.writestr(filename, png_bytes)

                generated_count += 1
                results.append(
                    {
                        "Index": idx,
                        "Filename": filename,
                        "Content": content_str[:40] + ("..." if len(content_str) > 40 else ""),
                        "Status": "✅ Success",
                        "Bytes": png_bytes,
                    }
                )
            except Exception as e:
                skipped_count += 1
                results.append(
                    {
                        "Index": idx,
                        "Filename": filename,
                        "Content": content_str[:40],
                        "Status": f"❌ Error: {str(e)}",
                        "Bytes": None,
                    }
                )

    zip_buffer.seek(0)

    return {
        "zip_bytes": zip_buffer.getvalue(),
        "total_generated": generated_count,
        "total_skipped": skipped_count,
        "items": results,
    }

