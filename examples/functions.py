import os

def add_text(text, html_path):
    op_str = text
    op_str = "<p >"+op_str+" "+"</p>"+"\n"
    write_content(op_str,html_path)

def add_table(table, html_path):
    op_str ="<p >"+" "+"</p>"+"\n"
    op_str += table
    write_content(op_str, html_path)
    

def write_content(content,output_path):
    with open(output_path,'a') as f:
        f.writelines(content)

def get_table(headers, data):
    content="<html>"+"<head>"+"<style>"
    content+="table, th, td {border: 1px solid black;border-collapse: collapse;border-spacing:8px}"
    content+="</style>"+"</head>"
    content+="<table style='width:50%'>"
    content+='<tr>'

    for i, header_name in enumerate(headers):
        content+="<th style='background-color:#3DBBDB;width:85;color:white'>"+header_name+"</th>"
        content+="</tr>"
        
        table_content="<tr style='text-align:center'>" 
        table_content += "<td>"+str(data[i])+"</td>"
        table_content+="<tr/>"
        content+=table_content

    content+="</table>"
    return(content)

def display_query(result):
    output_html = os.getcwd() + '//' + 'simon_result.html'
    add_text('Query Result', output_html)
    table = get_table(['ANSWER'], [result['answer']])
    add_table(table, output_html)
    source_key = list(result['answer_resources'].keys())
    table = get_table(['resource' + str(i+1) for i in source_key], ['Quote: ' + result['answer_resources'][i]['quote'] for i in source_key])
    add_table(table, output_html)

    print('Query Result: ', output_html)
    
    return 
