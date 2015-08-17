# coding: utf-8

# importing module located in parent folder
import sys
sys.path.insert(0, '../')

# maing testing library
import pyorcid as orcid

# additional libraries
import os
import json
import uuid
import codecs

# setting logging to the DEBUG mode
import logging

#logging.getLogger("orcid-bibtex-to-html").setLevel(logging.DEBUG)
logging.getLogger("orcid-bibtex-to-html").setLevel(logging.INFO)

TARGET_FODLER = 'generated'

UMLAUT_TO_LATEX = {
    u'Ö' : '\\"{O}',
    u'ö' : '\\"{o}',
    u'ä' : '\\"{a}',
    u'Ä' : '\\"{A}',
    u'Ü' : '\\"{U}',
    u'ü' : '\\"{u}',
    u'ß' : '{\\ss}'
}

def generate_bat(orcid_list, bat_name = 'buildall.{0}', separate=False, years = [], encoding='utf-8'):
    """
        (list, str, str) -> None

        Generating command bat file
    """

    cmd_comment = 'REM'
    cmd_file_name = bat_name.format('bat')
    cmd_env = 'set'
    cmd_path = '%PATH%;'
    path = 'C:\\Soft\\JabRef\\;'
    cmd_jabref = 'JabRef-2.10.jar'

    merge_files = 'copy /Y {0} "{1}".html\n'
    merge_file_internal = '"{0}-{1}.html"+'


    if os.name != 'nt':
        cmd_file_name = bat_name.format('sh')
        cmd_comment = '#'
        cmd_env = 'export'
        cmd_path = '$PATH;'
        path = '~/JabRef/'
        cmd_jabref = 'java -jar JabRef-2.10.jar'
        merge_files = 'cat {0} > "{1}".html\n'
        merge_file_internal = '"{0}-{1}.html" '


    cmd_header = '{0} SETTING PATH to JabRef\n'.format(cmd_comment)
    cmd_header += '{0} PATH={1}{2} \n\n'.format(cmd_env, cmd_path, path)

    #template = 'java -jar JabRef-2.10.jar -o "{0}".html,htmlvlba -n true "{0}".bib\n'
    if not separate:
        template = '{0} -o "{1}.html",htmlvlba -n true "{1}.bib"\n'
    else:
        template = '{0} -o "{1}-{2}.html",htmlvlba -n true "{1}-{2}.bib"\n'

    cmd = ''
    cmd_merge = ''

    for key in orcid_list:

        if not separate:
            cmd += template.format(cmd_jabref, key)
        else:
            merge_tmp = ''

            for x in years[key]:
                cmd += template.format(cmd_jabref, key, x)
                merge_tmp += merge_file_internal.format(key, x)


            cmd_merge += merge_files.format(merge_tmp[:-1], key)

    file_name = '{0}/{1}'.format(TARGET_FODLER, cmd_file_name)
    _file = codecs.open(file_name, 'w', encoding)
    _file.write(cmd_header)
    _file.write(cmd)
    _file.write('\n')

    # to merge htmls
    _file.write(cmd_merge)
    _file.close()


def save_bibtex(bibtex, file_prefix='orcid-bibtex-output', separate=False, encoding='utf-8'):
    """
        (dict, str, str) -> None

        - saving bibtex to the files, if required separating by year.
    """

    file_name = '{0}/{1}'.format(TARGET_FODLER, file_prefix)

    if not separate:
        _file = codecs.open(file_name + '.bib', 'w', encoding)

    for key in bibtex:

        if separate:
            _file = codecs.open(file_name + '-' + str(key) + '.bib', 'w', encoding)

        _file.write("%%%%%%%%%%%%%%%% \n%% %s \n%%%%%%%%%%%%%%%%\n\n" % key)

        bibtex_group = ''
        for value in bibtex[key]:
            bibtex_group += value + '\n\n'
        _file.write(bibtex_group)

        if separate:
            _file.close()

    if not separate:
        _file.close()


    print '[i] file with bibtex was created, check it here: %s ' % (file_name)

def form_bibtex(authors, title, year):
    """
        - forming bibtex
    """

    template = '@InProceedings{0}{2} , \n\t Title = {0}{3}{1}, \n\t Author = {0}{4}{1}, \n\t Year = {0}{5}{1}\n{1}'
    _authors = ' and '.join(authors)
    try:
        _title = title
        for x in UMLAUT_TO_LATEX:
            _title = _title.replace(x, UMLAUT_TO_LATEX[x])
    except Exception as ex:
        print '[i] exception happened'
        logging.exception('Working with umlauts.')
        _title = title

    return template.format('{','}', str(uuid.uuid1())[:13], _title, _authors, year)

def dump(obj):
  for attr in dir(obj):
    print "obj.%s = %s" % (attr, getattr(obj, attr))

def extract_bitex(obj, author):
    """
        (Class) -> dict()

        Method takes as an input object with all publications from ORCID and forms dict with it.
    """

    bibtex = {}
    nobibtex = list()

    for value in obj.publications:
        # from pprint import pprint
        # pprint(vars(value))
        # dump(value)
        try:
            if hasattr(value.citation, 'citation_type'):
                if value.citation.citation_type == 'BIBTEX':
                    if value.publicationyear not in bibtex:
                        bibtex[value.publicationyear] = list()
                        bibtex[value.publicationyear].append(value.citation.citation)
                    else:
                        bibtex[value.publicationyear].append(value.citation.citation)
                else:
                    nobibtex.append(form_bibtex([author], value.title, value.publicationyear))
                    print '[i] this publications is having no BIBTEX, new BIBTEX was generated {0}'.format(value.title)
            else:
                nobibtex.append(form_bibtex([author], value.title, value.publicationyear))
                print '[i] this publications is having no BIBTEX, new BIBTEX was generated {0}'.format(value.title)
        except Exception as ex:
            print '[i] exception happened'
            logging.exception('some exception with BIBTEX, new BIBTEX was generated {0}'.format(value.title))
            year = 0
            nobibtex.append(form_bibtex([author], value.title, year))

    if nobibtex:
        bibtex[99999] = nobibtex

    return bibtex

def main():
    """
        (list) -> None

        Extrating bibtex from ORCID, saving it to the file
    """

    separate_by_year = False

    import vlbalist as ol
    orcid_list = ol.orcid_list

    orcid_extracted = list()

    if not os.path.exists(TARGET_FODLER):
        os.makedirs(TARGET_FODLER)

    years = {}
    # extracting bibtex
    for key in orcid_list:

        name = key
        years[name] = list()
        orcidid = orcid_list[key]
        print '[i] extracting bibtex for {0}'.format(name)
        orcid_obj = orcid.get(orcidid)

        # extracting bibtex
        try:
            orcid_bibtex = extract_bitex(orcid_obj, author = name)

            # years
            tmp_list = list()
            for key in orcid_bibtex:
                tmp_list.append(key)
            years[name] = sorted(tmp_list, reverse = True)

            # saving bibtex into separated files
            save_bibtex(bibtex=orcid_bibtex, file_prefix=name, separate=separate_by_year)
            orcid_extracted.append(name)
        except Exception as ex:
            print '[i] exception happened'
            logging.exception('Caught and error')


    print  years
    generate_bat(orcid_extracted, separate=separate_by_year, years = years)

if __name__ == '__main__':

    # setting system default encoding to the UTF-8
    reload(sys)
    sys.setdefaultencoding('UTF8')

    # initiating main processing
    main()
