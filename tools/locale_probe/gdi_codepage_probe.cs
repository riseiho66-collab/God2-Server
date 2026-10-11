// Compare the process ANSI code page with the bytes that GDI TextOutA draws.
// The executable has no window and writes one result file supplied as argv[0].
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

internal static class GdiCodepageProbe {
    [DllImport("kernel32.dll")] static extern uint GetACP();
    [DllImport("gdi32.dll")] static extern IntPtr CreateCompatibleDC(IntPtr dc);
    [DllImport("gdi32.dll")] static extern bool DeleteDC(IntPtr dc);
    [DllImport("gdi32.dll")] static extern IntPtr CreateBitmap(int width,int height,uint planes,uint bits,IntPtr data);
    [DllImport("gdi32.dll")] static extern IntPtr SelectObject(IntPtr dc,IntPtr objectHandle);
    [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr objectHandle);
    [DllImport("gdi32.dll")] static extern IntPtr CreateFontW(int height,int width,int escapement,int orientation,
        int weight,uint italic,uint underline,uint strikeout,uint charset,uint precision,uint clipPrecision,
        uint quality,uint pitchAndFamily,string face);
    [DllImport("gdi32.dll")] static extern bool PatBlt(IntPtr dc,int x,int y,int width,int height,uint rop);
    [DllImport("gdi32.dll")] static extern uint SetTextColor(IntPtr dc,uint color);
    [DllImport("gdi32.dll")] static extern uint SetBkColor(IntPtr dc,uint color);
    [DllImport("gdi32.dll",EntryPoint="TextOutA")] static extern bool TextOutA(
        IntPtr dc,int x,int y,byte[] bytes,int count);
    [DllImport("gdi32.dll",CharSet=CharSet.Unicode,EntryPoint="TextOutW")] static extern bool TextOutW(
        IntPtr dc,int x,int y,string text,int count);
    [DllImport("gdi32.dll")] static extern uint GetPixel(IntPtr dc,int x,int y);

    static string Raster(IntPtr dc,byte[] bytes,string text) {
        if(!PatBlt(dc,0,0,200,60,0x00FF0062)) throw new Exception("PatBlt failed");
        bool ok=bytes!=null ? TextOutA(dc,4,4,bytes,bytes.Length) : TextOutW(dc,4,4,text,text.Length);
        if(!ok) throw new Exception("TextOut failed");
        ulong hash=14695981039346656037UL;
        unchecked {
            for(int y=0;y<60;y++) for(int x=0;x<200;x++) {
                hash^=GetPixel(dc,x,y);
                hash*=1099511628211UL;
            }
        }
        return hash.ToString("x16");
    }

    static int Main(string[] args) {
        if(args.Length!=1) return 2;
        IntPtr dc=IntPtr.Zero,bitmap=IntPtr.Zero,font=IntPtr.Zero,oldBitmap=IntPtr.Zero,oldFont=IntPtr.Zero;
        try {
            dc=CreateCompatibleDC(IntPtr.Zero);
            bitmap=CreateBitmap(200,60,1,32,IntPtr.Zero);
            font=CreateFontW(24,0,0,0,400,0,0,0,1,0,0,0,0,"Microsoft YaHei");
            if(dc==IntPtr.Zero || bitmap==IntPtr.Zero || font==IntPtr.Zero) throw new Exception("GDI setup failed");
            oldBitmap=SelectObject(dc,bitmap);oldFont=SelectObject(dc,font);
            SetTextColor(dc,0);SetBkColor(dc,0x00FFFFFF);
            const string expected="简体中文";
            byte[] gbk=Encoding.GetEncoding(936).GetBytes(expected);
            string twDecode=Encoding.GetEncoding(950).GetString(gbk);
            string a=Raster(dc,gbk,null),good=Raster(dc,null,expected),wrong=Raster(dc,null,twDecode);
            File.WriteAllText(args[0],"GetACP="+GetACP()+"\nCP936Bytes="+BitConverter.ToString(gbk)+
                "\nTextOutA="+a+"\nTextOutW_CP936="+good+"\nTextOutW_CP950="+wrong+
                "\nCP950Decoded="+twDecode+"\n",Encoding.UTF8);
            return 0;
        } catch(Exception error) {
            File.WriteAllText(args[0],"ERROR="+error+"\n",Encoding.UTF8);
            return 1;
        } finally {
            if(oldFont!=IntPtr.Zero && dc!=IntPtr.Zero) SelectObject(dc,oldFont);
            if(oldBitmap!=IntPtr.Zero && dc!=IntPtr.Zero) SelectObject(dc,oldBitmap);
            if(font!=IntPtr.Zero) DeleteObject(font);
            if(bitmap!=IntPtr.Zero) DeleteObject(bitmap);
            if(dc!=IntPtr.Zero) DeleteDC(dc);
        }
    }
}
