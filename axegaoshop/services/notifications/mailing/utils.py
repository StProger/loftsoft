import jinja2


def render_template(template, **kwargs):
    """renders a Jinja template into HTML"""
    templateLoader = jinja2.FileSystemLoader(
        searchpath="axegaoshop/services/notifications/mailing/templates/"
    )
    template_env = jinja2.Environment(loader=templateLoader)
    templ = template_env.get_template(template)
    return templ.render(**kwargs)
