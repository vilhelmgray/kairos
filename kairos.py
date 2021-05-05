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
import tkinter
from tkinter import ttk

class Kairos(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        master.title("Kairos")
        self.pack(fill='both', expand=True)
        self.timers = dict()
        self.create_widgets()
        self.update_eta()

    def destroy(self):
        self.refresher.cancel()
        for id in self.timers:
            self.timers[id].cancel()
        super().destroy()

    def create_widgets(self):
        self.deleteButton = ttk.Button(self, text="Delete",
                                       command=self.delete_tasks)
        self.deleteButton.pack(pady=5)

        self.schedule = ttk.Treeview(self)
        self.schedule['columns'] = ('name', 'command', 'eta', 'deadline')
        self.schedule['show'] = 'headings'
        self.schedule.bind('<<TreeviewSelect>>', self.select_task)
        self.schedule.bind('<Escape>', self.deselect_tasks)
        self.schedule.column('name', anchor = 'w')
        self.schedule.column('command', anchor = 'w')
        self.schedule.column('deadline', anchor='e')
        self.schedule.column('eta', anchor='e')
        self.schedule.heading('name', text='Name')
        self.schedule.heading('command', text='Command')
        self.schedule.heading('eta', text='ETA')
        self.schedule.heading('deadline', text='Deadline')
        self.schedule.pack(fill='both', expand=True, pady=5)

        self.addButton = ttk.Button(self, text="Add", command=self.add_task)
        self.addButton.pack(pady=5)

        self.add = ttk.Frame(self)
        self.add.pack(pady=5)

        self.add.name = ttk.LabelFrame(self.add, text="Name")
        self.add.name.pack(side='left', padx=5)
        self.add.name.str = tkinter.StringVar(self.add.name, "Unnamed")
        self.add.name.entry = ttk.Entry(self.add.name)
        self.add.name.entry['textvariable'] = self.add.name.str
        self.add.name.entry.pack()

        self.add.cmd = ttk.LabelFrame(self.add, text="Command")
        self.add.cmd.pack(side='left', padx=5)
        self.add.cmd.str = tkinter.StringVar(self.add.cmd)
        self.add.cmd.entry = ttk.Entry(self.add.cmd, width=50)
        self.add.cmd.entry['textvariable'] = self.add.cmd.str
        self.add.cmd.entry.pack()

        self.add.deadline = ttk.LabelFrame(self.add, text="Deadline")
        self.add.deadline.pack(side='left', padx=5)
        self.add.deadline.str = tkinter.StringVar(self.add.deadline)
        self.add.deadline.entry = ttk.Entry(self.add.deadline)
        self.add.deadline.entry['textvariable'] = self.add.deadline.str
        self.add.deadline.hours = ttk.Spinbox(self.add.deadline,
                                              to=sys.float_info.max)
        self.add.deadline.minutes = ttk.Spinbox(self.add.deadline,
                                                to=sys.float_info.max)
        self.add.deadline.seconds = ttk.Spinbox(self.add.deadline,
                                                to=sys.float_info.max)
        self.add.deadline.fmt = tkinter.IntVar()
        self.add.deadline.abs = ttk.Radiobutton(self.add.deadline,
                                                text="Absolute",
                                                variable=self.add.deadline.fmt,
                                                value=0,
                                                command=self.select_abs)
        self.add.deadline.abs.pack(side='left');
        self.add.deadline.rel = ttk.Radiobutton(self.add.deadline,
                                                text="Relative",
                                                variable=self.add.deadline.fmt,
                                                value=1,
                                                command=self.select_rel)
        self.add.deadline.rel.pack(side='left');
        self.add.deadline.abs.invoke()
        self.add.deadline.pack(side='left', padx=5)

        self.editButton = ttk.Button(self, text="Edit", command=self.edit_task)
        self.editButton.pack(pady=5)

    def execute_command(self, command, id):
        subprocess.run(command, shell=True)
        self.schedule.item(id, tags=('expired'))

    def select_task(self, e):
        id = self.schedule.focus()
        self.add.name.str.set(self.schedule.item(id)['values'][0])
        self.add.cmd.str.set(self.schedule.item(id)['values'][1])
        self.add.deadline.abs.invoke()
        self.add.deadline.str.set(self.schedule.item(id)['values'][3])

    def get_deadline(self):
        if self.add.deadline.fmt.get():
            delta = timedelta(hours=float(self.add.deadline.hours.get()),
                              minutes=float(self.add.deadline.minutes.get()),
                              seconds=float(self.add.deadline.seconds.get()))
            return datetime.now() + delta
        else:
            return datetime.strptime(self.add.deadline.str.get(), '%x %X')

    def deselect_tasks(self, e=None):
        self.schedule.selection_remove(self.schedule.selection())

    def edit_task(self):
        self.deselect_tasks()

        deadline = self.get_deadline()
        currTime = datetime.now()
        if deadline < currTime: return
        eta = deadline - currTime

        id = self.schedule.focus()
        command = self.add.cmd.str.get()
        self.schedule.set(id, 'name', self.add.name.str.get())
        self.schedule.set(id, 'command', command)
        self.schedule.set(id, 'deadline', deadline.strftime('%x %X'))
        self.schedule.item(id, tags=())

        self.timers[id].cancel()
        self.timers[id] = Timer(eta.total_seconds(), self.execute_command,
                                [command, id])
        self.timers[id].start()

    def add_task(self):
        self.deselect_tasks()

        deadline = self.get_deadline()
        currTime = datetime.now()
        if deadline < currTime: return
        eta = deadline - currTime

        command = self.add.cmd.str.get()
        id = self.schedule.insert('', 'end')
        self.schedule.set(id, 'name', self.add.name.str.get())
        self.schedule.set(id, 'command', command)
        self.schedule.set(id, 'deadline', deadline.strftime('%x %X'))
        self.schedule.tag_configure('expired', background='light pink')
        self.timers[id] = Timer(eta.total_seconds(), self.execute_command,
                                [command, id])
        self.timers[id].start()

    def delete_tasks(self):
        for selected in self.schedule.selection():
            self.timers[selected].cancel()
            self.schedule.delete(selected)

    def select_abs(self):
        currTime = datetime.now()
        self.add.deadline.str.set(currTime.strftime('%x %X'))
        self.add.deadline.hours.pack_forget()
        self.add.deadline.minutes.pack_forget()
        self.add.deadline.seconds.pack_forget()
        self.add.deadline.entry.pack()

    def select_rel(self):
        self.add.deadline.hours.delete(0, 'end')
        self.add.deadline.hours.insert(0, "0")
        self.add.deadline.minutes.delete(0, 'end')
        self.add.deadline.minutes.insert(0, "0")
        self.add.deadline.seconds.delete(0, 'end')
        self.add.deadline.seconds.insert(0, "0")
        self.add.deadline.entry.pack_forget()
        self.add.deadline.hours.pack()
        self.add.deadline.minutes.pack()
        self.add.deadline.seconds.pack()

    def update_eta(self):
        for id in self.schedule.get_children():
            # deadline is the 4th column
            deadlineStr = self.schedule.item(id)['values'][3]
            deadline = datetime.strptime(deadlineStr, '%x %X')
            currTime = datetime.now()
            if deadline > currTime:
                eta = deadline - currTime
            else:
                eta = currTime - deadline
            self.schedule.set(id, 'eta', str(eta).split('.')[0])
        self.refresher = Timer(1, self.update_eta)
        self.refresher.start()

root = tkinter.Tk()

kairos = Kairos(master=root)
kairos.mainloop()
