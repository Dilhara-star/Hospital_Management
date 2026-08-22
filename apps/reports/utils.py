from xhtml2pdf import pisa  # library that turns html text into a real pdf file
from django.template.loader import render_to_string  # turns a template + context into an html string
from django.http import HttpResponse  # lets us build our own http response (the pdf file)


# shared helper used by every report view below, so the pdf steps are written only once
def export_pdf(request, template_name, context, filename):
    # check if the user clicked the "Download PDF" button (adds ?download=pdf to the url)
    if request.GET.get('download') != 'pdf':
        return None  # they did not ask for a pdf, so give the view nothing to return

    html = render_to_string(template_name, context)  # turn the pdf template into an html string
    response = HttpResponse(content_type='application/pdf')  # start a response that is a pdf file
    response['Content-Disposition'] = f'attachment; filename="{filename}"'  # force a download prompt
    pisa.CreatePDF(html, dest=response)  # convert the html into a real pdf, written into the response
    return response  # give the finished pdf back to the view
