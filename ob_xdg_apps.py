#!/usr/bin/env python


import collections
import glob
from lxml import etree
import os
import gtk
from xdg.DesktopEntry import DesktopEntry


def main():
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
            comment = desktop_entry.getComment()
            if len(comment) > 0:
                name = '{}: {}'.format(name, comment)
            item_attributes = {'label': name}
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
            exec_ = desktop_entry.getExec()
            exec_ = exec_.split()[0]
            command.text = exec_

            if desktop_entry.getStartupNotify():
                startup_notify = etree.SubElement(action, 'startupnotify')
                enabled = etree.SubElement(startup_notify, 'enabled')
                enabled.text = 'yes'

    print etree.tostring(menu, pretty_print=True)


class MenuAccumulator(object):
    def __init__(self):

        main_categories = ('Audio', 'AudioVideo', 'Development', 'Education',
                           'Game', 'Graphics', 'Network', 'Office', 'Science',
                           'Settings', 'System', 'Utility', 'Video')
        self.__categories = collections.OrderedDict(
            (category, []) for category in main_categories)

    def add_entry(self, desktop_entry):
        if len(desktop_entry.getOnlyShowIn()) > 0:
            return
        if desktop_entry.getTerminal():
            return
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

    patterns = (
        os.path.join(os.sep, 'usr', 'share', 'applications', '*.desktop'),
        os.path.join(os.path.expanduser('~'),
                     '.local', 'share', 'applications', '*.desktop'))

    for pattern in patterns:
        for desktop_entry in glob.iglob(pattern):
            yield DesktopEntry(desktop_entry)

if __name__ == '__main__':
    main()
