class File(object):
    file = None
    filename = None
    def __init__(self, filename,mode='w'):
        self.file = open(filename, mode)
        self.filename = filename
    
    def read(self):
        return self.file.read()
     
    def readlines(self):
        return self.file.readlines()
     
    def writeln(self,*args):
        for arg in args:
            self.file.write(str(arg))
        self.file.write("\n")
    
    def write(self,*args):
        for arg in args:
            self.file.write(arg)
    
    def __del__(self):
        if self.file:
            self.file.close()
            self.file = None
    
    def close(self):
        """
        force file to be closed
        note that the file is automatically closed when they object is not referenced
        """
        if self.file:
            self.file.close()
            self.file = None
