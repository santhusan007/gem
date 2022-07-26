from customitem import Gem
if __name__=="__main__":
    src = "C:/Users/Admin/Downloads"
    dst = "D:/Gem2/"
    data=Gem(src,dst)
    #data.latestDownload()
    #data.move_file()
    # items=['CONTACT']
    # url = 'https://bidplus.gem.gov.in/custom-item'
    # data.itemwise_download(url,items)
    pdf_file_list=data.pdf_list()
    #pdf_file_list=pdf_file_list
    #data.data_to_csv(pdf_file_list)
    data.link_download(pdf_file_list)
    # data.move_pdf_file(pdf_file_list)
    

