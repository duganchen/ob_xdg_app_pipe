#!/usr/bin/env python


import collections
import glob
from lxml import etree
import os
import gtk
from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry


def main():
    cache_directory = BaseDirectory.save_cache_path('ob_xdg_apps')
    xml_file = os.path.join(cache_directory, 'menu.xml')

    appdirs = (os.path.join(datadir, 'applications') for datadir in
               BaseDirectory.xdg_data_dirs)

    if os.path.isfile(xml_file):
        updated = False
        for appdir in appdirs:
            if os.path.isdir(appdir):
                if os.stat(appdir).st_ctime > os.stat(xml_file).st_ctime:
                    updated = True
                    break

        if not updated:
            with open(xml_file) as f:
                print f.read()
            return

    icon_theme = gtk.icon_theme_get_default()

    menu = etree.Element('openbox_pipe_menu')
    menu_accumulator = MenuAccumulator()
    for desktop_entry in get_desktop_entries():
        menu_accumulator.add_entry(desktop_entry)
    menu_accumulator.finalize()

    categories = sorted(menu_accumulator.structure.keys())

    for category in categories:
        submenu_id = '{}-submenu'.format(category)
        submenu = etree.SubElement(menu, 'menu',
                                   {'id': submenu_id, 'label': category})

        for desktop_entry in menu_accumulator.structure[category]:
            name = desktop_entry.getName()
            item_attributes = {'label': name.decode('utf-8')}
            entry_icon = desktop_entry.getIcon()
            if os.path.isfile(entry_icon):
                item_attributes['icon'] = entry_icon
            else:
                icon_name = os.path.splitext(entry_icon)[0]
                icon_info = icon_theme.lookup_icon(icon_name, 48, 0)
                if icon_info is not None:
                    item_attributes['icon'] = icon_info.get_filename()
            item = etree.SubElement(submenu, 'item', item_attributes)
            action = etree.SubElement(item, 'action', {'name': 'Execute'})
            command = etree.SubElement(action, 'command')
            command.text = desktop_entry.getExec()

            if desktop_entry.getStartupNotify():
                startup_notify = etree.SubElement(action, 'startupnotify')
                enabled = etree.SubElement(startup_notify, 'enabled')
                enabled.text = 'yes'

    xml = etree.tostring(menu, pretty_print=True)
    with open(xml_file, 'w') as f:
        f.write(xml)
    print xml


class MenuAccumulator(object):
    def __init__(self):

        main_categories = ('Audio', 'AudioVideo', 'Development', 'Education',
                           'Game', 'Graphics', 'Network', 'Office', 'Science',
                           'Settings', 'System', 'Utility', 'Video')
        self.__categories = collections.OrderedDict(
            (category, []) for category in main_categories)

    def add_entry(self, desktop_entry):
        for category in desktop_entry.getCategories():
            if category in self.__categories:
                self.__categories[category].append(desktop_entry)
                break

    def finalize(self):
        for category, entries in self.__categories.iteritems():
            self.__categories[category] = sorted(
                entries, key=lambda x: x.getName().lower())
            if len(entries) == 0:
                del self.__categories[category]

    @property
    def structure(self):
        return self.__categories


MenuStructure = collections.namedtuple('MenuStructure',
                                       ['categories', 'uncategorized'])


def get_desktop_entries():

    starts = ((os.path.expanduser('~'), 'local'), (os.sep, 'usr'))
    end = ('share', 'applications', '*.desktop')

    for start in starts:
        pattern = os.path.join(*(start + end))

        for desktop_entry in glob.iglob(pattern):
            entry = DesktopEntry(desktop_entry)
            if entry.getNoDisplay():
                continue
            if entry.getOnlyShowIn():
                continue
            if entry.getTerminal():
                continue
            yield entry

if __name__ == '__main__':
    main()
