import cmd
import calendar

class calend(cmd.Cmd):
    prompt = "cal> "
    tc = calendar.TextCalendar()

    def do_pryear(self, arg):
        """ Print a month's calendar as returned by"""
        self.tc.pryear(int(arg))

    def do_prmonth(self, arg):
        """Print the calendar for an entire year"""
        self.tc.prmonth(*map(int, arg.split()))

    def do_EOF(self,arg):
        return True

if __name__ == "__main__":
    calend().cmdloop()
