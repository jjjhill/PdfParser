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
    # List of PDF URLs to download
    pdf_urls = [
        'https://www.cdms.net/ldat/ld9IL003.pdf',
        'https://www.cdms.net/ldat/ldBF4005.pdf',
        'https://www.cdms.net/ldat/ld6DE000.pdf',
        'https://www.cdms.net/ldat/ldATR001.pdf',
        'https://www.cdms.net/ldat/ld38T004.pdf',
        'https://www.cdms.net/ldat/ld6CU002.pdf',
        'https://www.cdms.net/ldat/ldH7J005.pdf',
        'https://www.cdms.net/ldat/ldDAD002.pdf',
        'https://www.cdms.net/ldat/ld3GR017.pdf',
        'https://www.cdms.net/ldat/ldAD6011.pdf',
        'https://www.cdms.net/ldat/ldCU4005.pdf',
        'https://www.cdms.net/ldat/ldB1Q004.pdf',
        'https://www.cdms.net/ldat/ldD2T000.pdf',
        'https://www.cdms.net/ldat/ldG9L000.pdf',
        'https://www.cdms.net/ldat/ldG9M000.pdf',
        'https://www.cdms.net/ldat/ld1RU006.pdf',
        'https://www.cdms.net/ldat/ld1S5003.pdf',
        'https://www.cdms.net/ldat/ldDAE002.pdf',
        'https://www.cdms.net/ldat/ldDAF005.pdf',
        'https://www.cdms.net/ldat/ld79H007.pdf',
        'https://www.cdms.net/ldat/ld8LE012.pdf',
        'https://www.cdms.net/ldat/ldB9L000.pdf',
        'https://www.cdms.net/ldat/ld95S004.pdf',
        'https://www.cdms.net/ldat/ld35G000.pdf',
        'https://www.cdms.net/ldat/ldDBS000.pdf',
        'https://www.cdms.net/ldat/ldDBT000.pdf',
        'https://www.cdms.net/ldat/ldDBU000.pdf',
        'https://www.cdms.net/ldat/ldE6S007.pdf',
        'https://www.cdms.net/ldat/ld6H2000.pdf',
        'https://www.cdms.net/ldat/ld9AM004.pdf',
        'https://www.cdms.net/ldat/ld62L013.pdf',
        'https://www.cdms.net/ldat/ld9NH006.pdf',
        'https://www.cdms.net/ldat/ldG64000.pdf',
        'https://www.cdms.net/ldat/ldEII000.pdf',
        'https://www.cdms.net/ldat/ldD90003.pdf',
        'https://www.cdms.net/ldat/ldAE8002.pdf',
        'https://www.cdms.net/ldat/ldAE6001.pdf',
        'https://www.cdms.net/ldat/ldAE7001.pdf',
        'https://www.cdms.net/ldat/ld9LO002.pdf',
        'https://www.cdms.net/ldat/ld8UD000.pdf',
        'https://www.cdms.net/ldat/ld34N002.pdf',
        'https://www.cdms.net/ldat/ldG9Q005.pdf',
        'https://www.cdms.net/ldat/ld9IA010.pdf',
        'https://www.cdms.net/ldat/ld9IA002.pdf',
        'https://www.cdms.net/ldat/ldASN005.pdf',
        'https://www.cdms.net/ldat/ldD8I000.pdf',
        'https://www.cdms.net/ldat/ldD8J000.pdf',
        'https://www.cdms.net/ldat/ld8DR003.pdf',
        'https://www.cdms.net/ldat/ld36F000.pdf',
        'https://www.cdms.net/ldat/ldDC8000.pdf',
        'https://www.cdms.net/ldat/ldBN1011.pdf',
        'https://www.cdms.net/ldat/ldG9N002.pdf',
        'https://www.cdms.net/ldat/ldGUT003.pdf',
        'https://www.cdms.net/ldat/ldC6K004.pdf',
        'https://www.cdms.net/ldat/ldC6J004.pdf',
        'https://www.cdms.net/ldat/ldCR7004.pdf',
    ]

    pdf_urls = ['https://www.cdms.net/ldat/ld9IA010.pdf']
    
    output_dir = "input_files"  # Directory to save the downloaded PDFs
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Download each PDF from the list
    for url in pdf_urls:
        download_pdf(url, output_dir)

if __name__ == "__main__":
    main()
