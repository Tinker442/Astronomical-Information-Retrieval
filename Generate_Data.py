import numpy as np
import os
import time
import requests

import json
# import urllib
from collections import defaultdict 
import PyPDF2
from io import BytesIO
from tqdm import tqdm
from PIL import Image

import astropy.units as u
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
from astropy.table import Table

from urllib.parse import urlencode
from astropy.io import fits
# from bs4 import BeautifulSoup
from crossref.restful import Works


import matplotlib.pyplot as plt


def get_full_text_from_bibcodes(bibcodes):
    output = []
    for i in range(min(number_of_docs,len(bibcodes))): 
        text=''
        works = Works()
        
        biblio = Simbad.query_bibcode(bibcodes[i])
        


        doi=biblio[0]['References'].split('\n')[0].split('=')[1][5:]
        # print(works.doi(doi)['abstract'])
        # time.sleep(1)

        # print(doi)
        # print(works.doi(doi))
        # print(works.doi(doi)['title'])
        # doi_url = works.doi(doi)['URL']
        doi_url = works.doi(doi)['link'][0]['URL']
        title = works.doi(doi)['title']
        # print(doi_url)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}
        response = requests.get(doi_url,headers=headers)
        # print(response)

        if(response.status_code!=200):
            print("Get failed with error :: ",response.status_code)
            continue
        

        with BytesIO(response.content) as data:
            read_pdf = PyPDF2.PdfReader(data)

            for page in range(len(read_pdf.pages)):
                text+=read_pdf.pages[page].extract_text()


        # for t in text.split('\n'):
        #     print(t)
        output.append((doi,title,text))

    # soup = BeautifulSoup(response.content, 'html.parser')
    # full_text = soup.get_text()
    # print(full_text.split('Abstract')[2].split('References')[0])
    return output
def get_abstract_from_bibcodes(bibcodes,num_docs):
    output = []
    for i in range(len(bibcodes)): 
        text=''
        works = Works()

        try:
            biblio = Simbad.query_bibcode(bibcodes[i])
        
            # try:
            doi=biblio[0]['References'].split('\n')[0].split('=')[1][5:]
            # except:
                # continue
            # try:
            doi_works=works.doi(doi)
            # except:
                # continue
            if 'abstract' not in doi_works or 'title' not in doi_works:
                continue
            text = doi_works['abstract']
            title = doi_works['title'][0]
            output.append((doi,title,text))
            if len(output)>=num_docs:
                break

            # time.sleep(0.1)
        except:
            continue
    return output
def get_object_from_hips(object, ra, dec,fov=0.1):
    query_params = { 
        'hips': 'DSS', 
        'object': object, 
        'ra': ra, 
        'dec': dec, 
        'fov': fov, 
        'width': 500, 
        'height': 500 
    }        

    url = f'https://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}' 
    # print(url)
    try:
        hdul = fits.open(url)  
    except:
        print("Failed to get image for ",object)
        return None
    # print(hdul.info())
    # print(hdul[0].data)
    image = hdul[0].data
    image= 255*((image-np.min(image))/(np.max(image)-np.min(image)))
    return image

if __name__ == "__main__":
    min_mag = 6.5
    
    # criteria = f'Bmag<{min_mag} | Vmag<{min_mag} | Rmag<{min_mag}'
    criteria = f'Bmag<{min_mag} | Vmag<{min_mag} | Rmag<{min_mag} | Gmag<{min_mag}'
    number_of_docs = 8
    query_history_path = "./data/raw_data/query_table.csv"
    object_types_path = "./data/raw_data/object_types.json"
    dataset_path = "./data/dataset.jsonl"
    images_path = "./data/images/"

    

    custom_simbad = Simbad()
    custom_simbad.add_votable_fields('biblio') #all references of object
    custom_simbad.add_votable_fields('ids') #all possible names of object
    custom_simbad.add_votable_fields('dim') #major axis size in arcmin
    custom_simbad.add_votable_fields('otype') #object type
    custom_simbad.add_votable_fields('flux(B)') #Blue magnitude
    custom_simbad.add_votable_fields('flux(V)') #Visual magnitude
    custom_simbad.add_votable_fields('flux(R)') #Red magnitude
    custom_simbad.add_votable_fields('flux(G)') #Green magnitude
    custom_simbad.TIMEOUT = 300


    # result_table = custom_simbad.query_object("Sirius")

    if os.path.exists(query_history_path):
        print("loading...")
        result_table = Table.read(query_history_path, format='ascii.csv')
        print(len(result_table))
    else:
        result_table = custom_simbad.query_criteria(criteria)
        print(len(result_table))
        result_table.write(query_history_path,format='ascii.csv')
    


    # print(result_table)
    # for key in list(result_table.keys()):
    #     print(key, result_table[0][key])

    if not os.path.exists(object_types_path):
        o_type_dict=defaultdict(int)
        for line in result_table:
            o_type_dict[line['OTYPE']]+=1
        with open(object_types_path,'w') as f:
            json.dump(o_type_dict,f,indent=1)



    dataset_file = open(dataset_path,'a')
    for i,result_line in tqdm(enumerate(result_table)):
        if i <=12500:
            continue
        
        try:
            object_main_id = result_line['MAIN_ID']#.encode('ascii')
            ra = result_line['RA']
            dec = result_line['DEC']
            bibcodes = result_line['BIBLIO'].split('|')
            ids = result_line['IDS'].split('|')
            o_type = result_line['OTYPE']
        except:
            continue

        mag_R = result_line['FLUX_R']
        mag_G = result_line['FLUX_G']
        mag_B = result_line['FLUX_B']
        mag_V = result_line['FLUX_V']
        magnitude = min([mag if mag != None else 100 for mag in [mag_R,mag_G,mag_B,mag_V]]) #brightest magnitude
        # print(magnitude)
        # print(bibcodes)

        # docs = get_full_text_from_bibcodes(bibcodes[:number_of_docs])
        docs = get_abstract_from_bibcodes(bibcodes,number_of_docs)
        # if len(docs)==0:
        #     continue
        # print(docs)

        dataset = {
            "object_number":i,
            "object_main_id":object_main_id,
            "ra":ra,
            "dec":dec,
            "mag":magnitude,
            "o_type":o_type,
            "ids": ids,
            "docs": docs
        }
        json.dump(dataset,dataset_file)
        dataset_file.write('\n')


        

        size = result_line['GALDIM_MAJAXIS']
        fov =  (size*1.2 * u.arcmin).to(u.deg).value
        if fov==0:
            fov = 0.2
            # fov=get_fov(object_main_id)
        # print(fov)
        
        object_coords = SkyCoord(ra=[ra], dec=[dec], 
                                unit=(u.hourangle, u.deg), frame='icrs')
        
        # print(object_coords)
        # print(object_main_id)

        image = get_object_from_hips(object_main_id,object_coords[0].ra.value,object_coords[0].dec.value,fov)
        if type(image) == type(None):
            continue
    
        plt.imsave(images_path+f'{i}.png',image,format='png', cmap='gray')
        


        
        # plt.figure()
        # plt.imshow(image, cmap='gray')
        # plt.colorbar()

        # plt.show()
    dataset_file.close()

