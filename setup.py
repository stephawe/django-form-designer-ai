# encoding=utf8

from setuptools import setup

setup(
    name='django-form-designer-ai',
    version='0.9.0',
    url='http://github.com/andersinno/django-form-designer-ai',
    license='BSD',
    maintainer='Anders Innovations Ltd',
    maintainer_email='info@anders.fi',
    packages=[
        'form_designer',
        'form_designer.migrations',
        'form_designer.templatetags',
        'form_designer.contrib',
        'form_designer.contrib.exporters',
        'form_designer.contrib.cms_plugins',
        'form_designer.contrib.cms_plugins.form_designer_form',
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    install_requires=[
        'django-picklefield>=0.3.2,<0.4',
    ],
)
