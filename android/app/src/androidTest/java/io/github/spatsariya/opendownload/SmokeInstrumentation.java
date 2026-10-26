package io.github.spatsariya.opendownload;
import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.os.*;
import java.net.*;
import java.io.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.Arrays;

public class SmokeInstrumentation extends Instrumentation {
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    @Override public void onStart(){
        Bundle result=new Bundle();long id=-1;DownloadManager manager=(DownloadManager)getTargetContext().getSystemService(Context.DOWNLOAD_SERVICE);
        MainActivity activity=null;
        try(ServerSocket server=new ServerSocket(0,4,InetAddress.getByName("127.0.0.1"))){
            final byte[] expected="OpenDownload Android integrity check".getBytes("UTF-8");
            Thread responder=new Thread(()->{try(Socket client=server.accept()){
                BufferedReader input=new BufferedReader(new InputStreamReader(client.getInputStream()));String line;while((line=input.readLine())!=null&&!line.isEmpty()){}
                OutputStream out=client.getOutputStream();out.write(("HTTP/1.1 200 OK\r\nContent-Length: "+expected.length+"\r\nContent-Type: application/octet-stream\r\nConnection: close\r\n\r\n").getBytes("US-ASCII"));out.write(expected);out.flush();
            }catch(Exception ignored){}});responder.setDaemon(true);responder.start();
            activity=(MainActivity)startActivitySync(new Intent(getTargetContext(),MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            if(activity.findViewById(R.id.main_root)==null)throw new AssertionError("Main UI did not launch");
            MainActivity target=activity;AtomicLong transfer=new AtomicLong();
            runOnMainSync(()->transfer.set(target.enqueue("http://127.0.0.1:"+server.getLocalPort()+"/check.bin")));id=transfer.get();
            boolean complete=false;
            for(int i=0;i<60;i++){try(Cursor c=manager.query(new DownloadManager.Query().setFilterById(id))){
                if(c.moveToFirst()){int status=c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));if(status==DownloadManager.STATUS_FAILED)throw new AssertionError("Download failed, reason="+c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON)));if(status==DownloadManager.STATUS_SUCCESSFUL){complete=true;break;}}
            }Thread.sleep(500);}
            if(!complete)throw new AssertionError("Download timed out");
            try(InputStream stream=new ParcelFileDescriptor.AutoCloseInputStream(manager.openDownloadedFile(id))){
                ByteArrayOutputStream data=new ByteArrayOutputStream();byte[] chunk=new byte[1024];int count;while((count=stream.read(chunk))!=-1)data.write(chunk,0,count);
                if(!Arrays.equals(expected,data.toByteArray()))throw new AssertionError("Downloaded bytes differ");
            }
            result.putString("stream","DOWNLOAD_SMOKE_OK\n");finish(Activity.RESULT_OK,result);
        }catch(Throwable e){result.putString("stream","DOWNLOAD_SMOKE_FAILED: "+e+"\n");finish(Activity.RESULT_CANCELED,result);}
        finally{if(id!=-1)manager.remove(id);if(activity!=null){MainActivity last=activity;runOnMainSync(last::finish);}}
    }
}
