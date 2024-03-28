from jinja2 import Template, StrictUndefined

with open("templates/template.html", "r") as template_file:
    template = Template(template_file.read(), undefined=StrictUndefined)
template.stream(**data).dump("<++>.html")
