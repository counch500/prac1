import cmd
import calendar

class calend(cmd.Cmd):
    prompt = "cal> "
    tc = calendar.TextCalendar()
    Month = {m.name: m.value for m in calendar.Month}

    def do_pryear(self, arg):
        """ Print a month's calendar as returned by"""
        self.tc.pryear(int(arg))

    def do_prmonth(self, arg):
        """Print the calendar for an entire year"""
        year, month = arg.split()
        self.tc.prmonth(int(year), self.Month[month])
    def complete_prmonth(self, text, line, begidx, endidx):
        return [m for m in self.Month if m.startswith(text)]

    def do_EOF(self,arg):
        return True

if __name__ == "__main__":
    calend().cmdloop()




