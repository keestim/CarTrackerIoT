from subprocess import call

cmd_beg= 'espeak '
cmd_end= ' 2>/dev/null' # To dump the std errors to /dev/null

cmd = "High RPM. Consider choosing a higher gear"

print(cmd_beg + cmd + cmd_end)

#need to isolate in it's own thread!
call([cmd_beg + '"' + cmd + '"' + cmd_end], shell=True)
