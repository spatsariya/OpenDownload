package io.github.spatsariya.opendownload;

import android.app.*;
import android.os.*;
import android.content.*;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.view.*;
import android.widget.*;
import org.json.JSONArray;
import java.util.*;

public class MainActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ArrayList<Long> ids = new ArrayList<>();
    private DownloadManager downloads;
    private LinearLayout list;
    private TextView summary;
    private final Runnable refresh = new Runnable() {
        public void run() { render(); handler.postDelayed(this, 1500); }
    };
    private int dp(int n) { return (int)(n * getResources().getDisplayMetrics().density); }
    private TextView text(String value, int size, int color) {
        TextView view=new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(color); return view;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        downloads=(DownloadManager)getSystemService(DOWNLOAD_SERVICE);
        try {
            JSONArray saved=new JSONArray(getPreferences(0).getString("ids","[]"));
            for (int i=0;i<saved.length();i++) ids.add(saved.getLong(i));
        } catch(Exception ignored) {}
        LinearLayout root=new LinearLayout(this); root.setId(1001); root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(249,251,254)); root.setPadding(dp(20),dp(28),dp(20),dp(16));
        root.setOnApplyWindowInsetsListener((v,insets)->{v.setPadding(dp(20),insets.getSystemWindowInsetTop()+dp(20),dp(20),insets.getSystemWindowInsetBottom()+dp(12));return insets;});
        TextView title=text("OpenDownload",27,Color.rgb(28,44,67)); title.setTypeface(null,Typeface.BOLD);root.addView(title);
        summary=text("Your downloads, in one place.",13,Color.rgb(105,121,143));summary.setPadding(0,dp(8),0,dp(20));root.addView(summary);
        Button add=new Button(this);add.setText("+  Add download");add.setAllCaps(false);add.setTextColor(Color.WHITE);
        GradientDrawable bg=new GradientDrawable();bg.setColor(Color.rgb(52,120,246));bg.setCornerRadius(dp(12));add.setBackground(bg);
        root.addView(add,new LinearLayout.LayoutParams(-1,dp(48)));add.setOnClickListener(v->addDialog());
        TextView hint=text("ANDROID PREVIEW  ·  Files save to Downloads",11,Color.rgb(112,128,148));hint.setPadding(0,dp(20),0,dp(14));root.addView(hint);
        ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
    }
    @Override public void onResume(){super.onResume();handler.post(refresh);}
    @Override public void onPause(){handler.removeCallbacks(refresh);super.onPause();}
    private void save(){getPreferences(0).edit().putString("ids",new JSONArray(ids).toString()).apply();}
    private void addDialog(){
        EditText input=new EditText(this);input.setHint("https://example.com/file.zip");input.setSingleLine(true);input.setInputType(17);
        LinearLayout holder=new LinearLayout(this);holder.setPadding(dp(20),dp(6),dp(20),0);holder.addView(input,new LinearLayout.LayoutParams(-1,-2));
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Add download").setView(holder).setNegativeButton("Cancel",null).setPositiveButton("Download",null).create();
        dialog.setOnShowListener(v->dialog.getButton(-1).setOnClickListener(w->{try{enqueue(input.getText().toString().trim());dialog.dismiss();render();}catch(Exception e){input.setError(e.getMessage());}}));dialog.show();
    }
    public long enqueue(String url){
        Uri uri=Uri.parse(url);
        if (!("https".equalsIgnoreCase(uri.getScheme())||"http".equalsIgnoreCase(uri.getScheme())) || uri.getHost()==null) throw new IllegalArgumentException("Enter a complete HTTP or HTTPS link.");
        String name=uri.getLastPathSegment();if(name==null||name.isEmpty())name="download";
        name=name.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]","_");if(name.length()>150)name=name.substring(0,150);
        String unique="OpenDownload-"+UUID.randomUUID().toString().substring(0,8)+"-"+name;
        DownloadManager.Request request=new DownloadManager.Request(uri).setTitle(name).setDescription("OpenDownload")
            .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS,unique)
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
        long id=downloads.enqueue(request);ids.add(0,id);save();return id;
    }
    private String bytes(long n){return n<0?"Unknown":n>=1048576?String.format(Locale.US,"%.1f MB",n/1048576.0):String.format(Locale.US,"%.1f KB",n/1024.0);}
    private void render(){
        if(list==null)return;list.removeAllViews();summary.setText(ids.size()+" downloads · Managed by Android");
        if(ids.isEmpty()){TextView empty=text("No downloads yet\nAdd a direct file link to get started.",15,Color.rgb(118,132,150));empty.setPadding(0,dp(42),0,0);empty.setGravity(Gravity.CENTER);list.addView(empty);return;}
        for(long id:new ArrayList<>(ids)){
            try(Cursor c=downloads.query(new DownloadManager.Query().setFilterById(id))){
                if(c==null||!c.moveToFirst())continue;
                String title=c.getString(c.getColumnIndexOrThrow(DownloadManager.COLUMN_TITLE));
                int status=c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));
                long done=c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR));
                long total=c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES));
                String state=status==DownloadManager.STATUS_SUCCESSFUL?"Complete":status==DownloadManager.STATUS_FAILED?"Failed":status==DownloadManager.STATUS_PAUSED?"Waiting for network":status==DownloadManager.STATUS_PENDING?"Queued":"Downloading";
                LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.VERTICAL);row.setPadding(dp(14),dp(14),dp(14),dp(14));
                GradientDrawable shape=new GradientDrawable();shape.setColor(Color.WHITE);shape.setCornerRadius(dp(12));shape.setStroke(dp(1),Color.rgb(229,235,244));row.setBackground(shape);
                LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2);params.bottomMargin=dp(10);list.addView(row,params);
                TextView name=text(title,15,Color.rgb(32,49,72));name.setMaxLines(2);row.addView(name);
                TextView info=text(state+"  ·  "+bytes(done)+" / "+bytes(total),12,Color.rgb(83,111,150));info.setPadding(0,dp(7),0,dp(9));row.addView(info);
                ProgressBar progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setMax(100);progress.setProgress(total>0?(int)Math.min(100,100.0*done/total):0);row.addView(progress);
                row.setOnClickListener(v->{if(status==DownloadManager.STATUS_SUCCESSFUL)open(id);});
                row.setOnLongClickListener(v->{new AlertDialog.Builder(this).setTitle("Remove download?").setMessage("This cancels the transfer and deletes its downloaded file.").setNegativeButton("Keep",null).setPositiveButton("Remove",(d,w)->{downloads.remove(id);ids.remove(id);save();render();}).show();return true;});
            }catch(Exception e){Toast.makeText(this,"Cannot read download status",Toast.LENGTH_SHORT).show();break;}
        }
    }
    private void open(long id){try{Uri uri=downloads.getUriForDownloadedFile(id);if(uri==null)return;String type=downloads.getMimeTypeForDownloadedFile(id);startActivity(new Intent(Intent.ACTION_VIEW).setDataAndType(uri,type==null?"*/*":type).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION));}catch(ActivityNotFoundException e){Toast.makeText(this,"No app can open this file",Toast.LENGTH_SHORT).show();}}
}
