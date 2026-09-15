from requests import status_codes
from urllib import response
import os 
import sys
import requests
from bs4 import BeautifulSoup # web scrapping

def download_image(url,save_path):
    # this tries to get data from the website and save it to the specified path
    response=requests.get(url)

    if response.status_code == 200:

        #open a new file on your computer in 'wb' (write binary) mode
        #because image se binary files , not text.requests
        with open(save_path,'wb') as file:
            # this will take the binary data from the response

            #write the raw binary data from the website into our new file 
            file.write(response.content) 
        print(f'saved image to {save_path} successfully')
        return True
    else:
        print("Failed to Download image. Status code: ", response.status_code)
        return False

def try_openlibrary(book_name,save_path):
    print(f"Searching for '{book_name}' on OpenLibrary...")

    # 1. We search the OpenLibrary API to get the ISBN for this book name
    search_url = f"http://openlibrary.org/search.json?title={book_name.replace(' ', '+')}"
    response = requests.get(search_url)

    if response.status_code == 200:
        data = response.json()
        if data.get('docs') and len(data['docs']) > 0:
            isbns = data['docs'][0].get('isbn', [])
            if isbns:
                isbn = isbns[0]
                # we create the specific URL for this ISBN using an f-string
                url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

                # 2 Calling download Function  from Step 2
                # because your function returns True or False , we can put it in an 'if' statement .
                success = download_image(url,save_path)

                if success == True:
                    #  3. OpenLibrary is super reliable , but if it fails 
                    # it gives us a tiny blank image (< 1000 bytes) instead of an error.
                    # using 'OS' lib to check imported file size.True
                    file_size = os.path.getsize(save_path)
                    if file_size > 1000:
                        print(f"Found Cover page for '{book_name}' On OpenLibrary !")
                        return True
                    else:
                        print(f"Could not Find Cover page for '{book_name}' on OpenLibrary (Image too small)")
                        os.remove(save_path)
                        return False
        print(f"Could not Find Cover page for '{book_name}' on OpenLibrary")
    else:
        print(f"Failed to connect to OpenLibrary API")
    return False

def try_amazon_scrape(book_name,save_path):

    print(f"Method 2 : Scraping Amazon.in for '{book_name}'...")
    
    #1.URL for Amazon Search
    search_url = f"https://www.amazon.in/s?k={book_name.replace(' ', '+')}"
    
    #2. Amazons website blocks normal Python code (called 'User-Agent').
    # Amazon blocks bots. We use "headers" to trick Amazon into thinking we are 
    # a real human using Google Chrome on Windows.
    # Headers essentially tell the server: "Hey, I'm using Chrome on Windows, not a robot."
    
    headers = {

        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36'
    }
    # This is the HTTP Header (or 'Header').
    # Amazon is very strict. If you don't send this header, Amazon will ignore your request and send back nothing. 
    # This specific text makes your computer pretend to be a normal Google Chrome browser.

    #Send the request 
    # We add 'headers = headers' to include the disguise we created above.
  
    response=requests.get(search_url,headers=headers)
  
    if response.status_code== 200:
    #3 we had hand the raw HTML to Beautifulsoup to organize it 

      soup = BeautifulSoup(response.content,'html.parser')

      #4. To get the actual cover image , we need to find the 'img' tag 
      # which Amazon puts product images inside an <img> tag with a class called "s-image"

      # this is a command for the computer to search through the organized HTML
      # and find the FIRST image that has the class "s-image" 
   
      img_tag = soup.find('img',class_='s-image')

      if img_tag != None:
      #Amazon image url are sometimes incomplete (they miss 'https:').
      # this line ensures the URL starts with 'https:' before we try to download it
         img_url= img_tag['src']
         high_res_url = img_url.split('._')[0] + '.jpg'
         print(f"Found image on Amazon! URL: {high_res_url}")

        #5.we call download function again 
         success = download_image(high_res_url,save_path)
         if success == True:
          print("Found Cover page for" ,book_name, "on Amazon!")
          return True
         else:
          return False
      else:
        print("No image found on Amazon")
        return False

def try_google_books(book_name,save_path):
    print(f"Method 3 : Searching Google Books for '{book_name}'...")
    api_url = f'https://www.googleapis.com/books/v1/volumes?q=intitle:{book_name.replace(" ", "+")}'        

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            volume_info = data['items'][0].get('volumeInfo', {})
            image_links = volume_info.get('imageLinks', {})
            img_url = image_links.get('thumbnail')
            
            if img_url:
                print(f"Found image on Google Books! URL: {img_url}")
                success = download_image(img_url, save_path)
                if success == True:
                    print("Found Cover page for" ,book_name, "on Google Books!")
                    return True
                else:
                    return False
            else:
                print("No image thumbnail found on Google Books")
                return False
        else:
            print("Book not found on Google Books")
            return False
    else:
        print("Failed to connect to Google Books API")
        return False




def download_cover(book_name,output_dir):
    # 1. This cleans up the book name for the file path
    clean_name = book_name.strip().replace(" ", "_")

    #2. we use 'OS' to automatically create a folder to stoe our images
    os.makedirs(output_dir, exist_ok=True)
    
    #3. Here is where we define thet famous 'save_path' !
    # os.path.join safely connects folder and file name 

    save_path = os.path.join(output_dir, f'{clean_name}.jpg')

    print(f"\n---- Starting Download Process For : '{book_name}'----\n")
    
    # 1st approch :OpenLibrary
    success = try_openlibrary(book_name,save_path)

    if success == True:
        return save_path
    
    #2nd approch :Amazon (Scraping)     
    success = try_amazon_scrape(book_name,save_path)       

    if success == True:
        return save_path
        
    #3rd approch :Google Books
    success = try_google_books(book_name,save_path)

    if success == True:
        return save_path
    
    print(f"Failed to Download cover for '{book_name}' after trying all methods.")
    return None 

if __name__ == "__main__":

    # sys.argv is the list of arguments passed to the script from the terminal
    
    if len(sys.argv)<2 :
        print("Error: You forgot to type a Book Name!")
        print('Usage Example : python cover_downloader_by_name.py "The Psychology of Money"')
        sys.exit()

    # 2. If the user DID type a Book Name , we grab it.
    # sys.argv[0] is the script name , sys.argv[1] is the first argument
    else:
          book_name_input = sys.argv[1]

    # 3. We specify a folder where the image will be saved
          download_cover(book_name_input, "my_cool_covers")
