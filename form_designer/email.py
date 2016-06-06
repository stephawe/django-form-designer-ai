import re
from django.core.mail import EmailMessage


def build_form_mail(form_definition, form, files=None):
    """
    Build a form-submission email based on the given form definition and associated submitted form

    :param form_definition: Form definition object
    :param form: The freshly submitted form
    :param files: Associated files
    :return: Django email message
    """
    if not files:
        files = []
    form_data = form_definition.get_form_data(form)
    message = form_definition.compile_message(form_data)
    context_dict = form_definition.get_form_data_context(form_data)

    mail_to = re.compile('\s*[,;]+\s*').split(form_definition.mail_to)
    for key, email in enumerate(mail_to):
        mail_to[key] = form_definition.string_template_replace(email, context_dict)

    mail_from = form_definition.mail_from or None
    if mail_from:
        mail_from = form_definition.string_template_replace(mail_from, context_dict)

    if form_definition.mail_subject:
        mail_subject = form_definition.string_template_replace(form_definition.mail_subject, context_dict)
    else:
        mail_subject = form_definition.title

    message = EmailMessage(mail_subject, message, mail_from or None, mail_to)
    if form_definition.is_template_html:
        message.content_subtype = "html"

    if form_definition.mail_uploaded_files:
        for file_path in files:
            message.attach_file(file_path)

    return message
