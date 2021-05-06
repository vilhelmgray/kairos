#!/usr/bin/env python3
# Copyright (C) 2020 William Breathitt Gray
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import datetime, timedelta
import subprocess
import sys
from threading import Timer
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

class Kairos(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Kairos", default_height=480, default_width=640)
        self.connect("destroy", self.destroy)
        self.set_border_width(10)

        self.timers = dict()
        self.create_widgets()
        GLib.timeout_add(1000, self.update_eta)

    def destroy(self, widget):
        for stamp in self.timers:
            self.timers[stamp].cancel()
        Gtk.main_quit()

    def create_widgets(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        deleteButton = Gtk.Button(label="Delete")
        deleteButton.connect("clicked", self.delete_tasks)
        vbox.pack_start(deleteButton, False, False, 0)

        scrolledWindow = Gtk.ScrolledWindow()
        vbox.pack_start(scrolledWindow, True, True, 0)

        self.schedule = Gtk.ListStore(str, str, str, str, str)
        tasksView = Gtk.TreeView(model=Gtk.TreeModelSort(model=self.schedule))
        self.selection = tasksView.get_selection()
        self.selection.connect("changed", self.select_task)
        self.selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        renderer = Gtk.CellRendererText()
        deadlineColumn = Gtk.TreeViewColumn("Deadline", renderer, text=0)
        deadlineColumn.set_sort_column_id(0)
        deadlineColumn.set_sort_indicator(True)
        etaColumn = Gtk.TreeViewColumn("ETA", renderer, text=1, background=2)
        etaColumn.set_sort_column_id(1)
        etaColumn.set_sort_indicator(True)
        nameColumn = Gtk.TreeViewColumn("Name", renderer, text=3)
        nameColumn.set_resizable(True)
        nameColumn.set_sort_column_id(3)
        nameColumn.set_sort_indicator(True)
        commandColumn = Gtk.TreeViewColumn("Command", renderer, text=4)
        commandColumn.set_resizable(True)
        tasksView.append_column(deadlineColumn)
        tasksView.append_column(etaColumn)
        tasksView.append_column(nameColumn)
        tasksView.append_column(commandColumn)
        scrolledWindow.add(tasksView)

        addButton = Gtk.Button(label="Add")
        addButton.connect("clicked", self.add_task)
        vbox.pack_start(addButton, False, False, 0)

        addBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(addBox, False, False, 0)

        nameBox = Gtk.Box(spacing=6)
        addBox.pack_start(nameBox, False, False, 0)
        nameLabel = Gtk.Label(label="Name:")
        self.nameEntry = Gtk.Entry()
        nameBox.pack_start(nameLabel, False, False, 0)
        nameBox.pack_start(self.nameEntry, True, True, 0)

        cmdBox = Gtk.Box(spacing=6)
        addBox.pack_start(cmdBox, False, False, 0)
        cmdLabel = Gtk.Label(label="Command:")
        self.cmdEntry = Gtk.Entry()
        cmdBox.pack_start(cmdLabel, False, False, 0)
        cmdBox.pack_start(self.cmdEntry, True, True, 0)

        deadlineBox = Gtk.Box(spacing=6)
        addBox.pack_start(deadlineBox, True, True, 0)
        deadlineLabel = Gtk.Label(label="Deadline:")
        self.absRadio = Gtk.RadioButton.new_with_label_from_widget(None, "Absolute")
        self.absRadio.connect("toggled", self.select_abs)
        relRadio = Gtk.RadioButton.new_with_label_from_widget(self.absRadio, "Relative")
        relRadio.connect("toggled", self.select_rel)
        self.absBox = Gtk.Box(spacing=6)
        self.deadlineEntry = Gtk.Entry()
        self.absBox.pack_start(self.deadlineEntry, True, True, 0)
        self.relBox = Gtk.Box(spacing=6)
        hoursBox = Gtk.Box(spacing=6)
        hoursLabel = Gtk.Label(label="Hours")
        self.hoursSpin = Gtk.SpinButton.new_with_range(0, sys.float_info.max, 1)
        hoursBox.pack_start(hoursLabel, False, False, 0)
        hoursBox.pack_start(self.hoursSpin, False, False, 0)
        minutesBox = Gtk.Box(spacing=6)
        minutesLabel = Gtk.Label(label="Minutes")
        self.minutesSpin = Gtk.SpinButton.new_with_range(0, sys.float_info.max, 1)
        minutesBox.pack_start(minutesLabel, False, False, 0)
        minutesBox.pack_start(self.minutesSpin, False, False, 0)
        secondsBox = Gtk.Box(spacing=6)
        secondsLabel = Gtk.Label(label="Seconds")
        self.secondsSpin = Gtk.SpinButton.new_with_range(0, sys.float_info.max, 1)
        secondsBox.pack_start(secondsLabel, False, False, 0)
        secondsBox.pack_start(self.secondsSpin, False, False, 0)
        self.relBox.pack_start(hoursBox, False, False, 0)
        self.relBox.pack_start(minutesBox, False, False, 0)
        self.relBox.pack_start(secondsBox, False, False, 0)
        deadlineBox.pack_start(deadlineLabel, False, False, 0)
        deadlineBox.pack_start(self.absRadio, False, False, 0)
        deadlineBox.pack_start(relRadio, False, False, 0)
        deadlineBox.pack_start(self.absBox, True, True, 0)
        deadlineBox.pack_start(self.relBox, False, False, 0)

        editButton = Gtk.Button(label="Edit")
        editButton.connect("clicked", self.edit_task)
        vbox.pack_start(editButton, False, False, 0)

        self.show_all()
        self.select_abs(self.absRadio)

    def execute_command(self, task, command):
        self.schedule[task][2] = "light pink"
        subprocess.run(command, shell=True)

    def select_task(self, selection):
        if not self.selection.count_selected_rows():
            return
        (schedule, paths) = self.selection.get_selected_rows()
        selected = schedule.get_iter(paths[0])
        self.absRadio.set_active(True)
        self.deadlineEntry.set_text(schedule[selected][0])
        self.nameEntry.set_text(schedule[selected][3])
        self.cmdEntry.set_text(schedule[selected][4])

    def get_deadline(self):
        if self.absRadio.get_active():
            return datetime.strptime(self.deadlineEntry.get_text(), '%x %X')
        else:
            delta = timedelta(hours=self.hoursSpin.get_value(),
                              minutes=self.minutesSpin.get_value(),
                              seconds=self.secondsSpin.get_value())
            return datetime.now() + delta

    def edit_task(self, widget):
        deadline = self.get_deadline()
        currTime = datetime.now()
        if deadline < currTime: return
        eta = deadline - currTime

        if not self.selection.count_selected_rows():
            return
        paths = self.selection.get_selected_rows()[1]
        task = self.schedule.get_iter(paths[0])
        self.selection.unselect_all()

        self.schedule[task][0] = deadline.strftime('%x %X')
        self.schedule[task][1] = str(eta).split('.')[0]
        self.schedule[task][3] = self.nameEntry.get_text()
        command = self.cmdEntry.get_text()
        self.schedule[task][4] = command

        self.timers[task.user_data].cancel()
        self.timers[task.user_data] = Timer(eta.total_seconds(), self.execute_command, [task, command])
        self.timers[task.user_data].start()

    def add_task(self, widget):
        deadline = self.get_deadline()
        currTime = datetime.now()
        if deadline < currTime: return
        eta = deadline - currTime

        self.selection.unselect_all()

        deadline = deadline.strftime('%x %X')
        name = self.nameEntry.get_text()
        command = self.cmdEntry.get_text()
        task = self.schedule.append([deadline, str(eta).split('.')[0], "white", name, command])
        self.timers[task.user_data] = Timer(eta.total_seconds(), self.execute_command, [task, command])
        self.timers[task.user_data].start()

    def delete_tasks(self, widget):
        refs = []
        for path in self.selection.get_selected_rows()[1]:
            refs.append(Gtk.TreeRowReference.new(self.schedule, path))
        for ref in refs:
            task = self.schedule.get_iter(ref.get_path())
            self.timers[task.user_data].cancel()
            del self.timers[task.user_data]
            self.schedule.remove(task)

    def select_abs(self, widget):
        self.relBox.hide()
        currTime = datetime.now()
        self.deadlineEntry.set_text(currTime.strftime('%x %X'))
        self.absBox.show()

    def select_rel(self, widget):
        self.absBox.hide()
        self.hoursSpin.set_value(0)
        self.minutesSpin.set_value(0)
        self.secondsSpin.set_value(0)
        self.relBox.show()

    def update_eta(self):
        for row in self.schedule:
            deadline = datetime.strptime(row[0], '%x %X')
            currTime = datetime.now()
            if deadline > currTime:
                eta = deadline - currTime
            else:
                eta = currTime - deadline
            row[1] = str(eta).split('.')[0]
        return True

kairos = Kairos()
Gtk.main()
