import requests
import os

def download_pdf(url, output_dir):
    # Extract filename from the URL
    filename = url.split("/")[-1]
    # Construct the full output path
    output_path = os.path.join(output_dir, filename)

    # Make the request to download the PDF file
    response = requests.get(url)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Write the content to the output file
        with open(output_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download: {filename}")

def main():
    # PDF links here separated by commas
    # Ex.
    pdf_urls = [
        # 'https://www.cdms.net/ldat/ld9IA010.pdf',
        # 'https://www.cdms.net/ldat/ld9IA011.pdf',
    ]
    
    output_dir = "input_files"  # Directory to save the downloaded PDFs
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Download each PDF from the list
    for url in pdf_urls:
        download_pdf(url, output_dir)

if __name__ == "__main__":
    main()
