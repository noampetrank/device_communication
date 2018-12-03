package com.buga.rpcsoloader;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.TextView;

public class RpcSoLoaderActivity extends AppCompatActivity {

    // Used to load the 'buga_rpc_loader' library on application startup.
    static {
        System.loadLibrary("native-lib");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_rpc_so_loader);

        // Example of a call to a native method
        TextView tv = (TextView) findViewById(R.id.sample_text);
        tv.setText(startRpcSoLoader(getApplicationInfo().nativeLibraryDir));
    }

    /**
     * A native method that is implemented by the 'native-lib' native library,
     * which is packaged with this application.
     */
    public native String startRpcSoLoader(String libsPAth);
}
