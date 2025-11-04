from app.utils.pdf_extractor import extract_ndpr_text

if __name__ == "__main__":
    extract_ndpr_text("app/data/NDPR-Implementation-Framework.pdf", "app/data/ndpr_full_text.txt")
    print("NDPR text extracted successfully.")
