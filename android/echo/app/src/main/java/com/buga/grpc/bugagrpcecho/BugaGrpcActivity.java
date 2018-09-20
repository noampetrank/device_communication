package com.buga.grpc.bugagrpcecho;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.support.annotation.Keep;
import android.support.v7.app.AppCompatActivity;
import android.text.TextUtils;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import com.buga.grpc.cpp.BugaGrpc;
import com.buga.grpc.cpp.BugaRpcExecutor;
import com.buga.grpc.cpp.MarshaledObject;

public class BugaGrpcActivity extends AppCompatActivity {

    private BugaGrpc grpc = new BugaGrpc();
    private Button serverButton;
    private EditText serverPortEdit;

    private int DEFAULT_PORT = 60004;
    private boolean isServerStarted = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_buga_grpc);
        serverButton = (Button) findViewById(R.id.server_button);
        serverPortEdit = (EditText) findViewById(R.id.server_port_edit_text);
        serverPortEdit.setHint("Server port (default " + DEFAULT_PORT + ")");
        grpc.registerExecutor(new BugaEchoExecutor());
    }

    @Override
    protected void onPause() {
        super.onPause();
    }

    public void startOrStopServer(View view) {
        if (isServerStarted) {
            grpc.stopServer();
            isServerStarted = false;
        } else {
            isServerStarted = grpc.startServer(port());
        }
        serverButton.setText((isServerStarted?"Stop":"Start") + " gRPC Server");
        Toast.makeText(BugaGrpcActivity.this, "Server " + (isServerStarted?"started":"stopped") + " on port " + port(), Toast.LENGTH_LONG).show();
    }

    private int port() {
        String portStr = serverPortEdit.getText().toString();
        return TextUtils.isEmpty(portStr) ? DEFAULT_PORT : Integer.valueOf(portStr);
    }

    Handler mHandler = new Handler(Looper.getMainLooper()) {
        @Override
        public void handleMessage(Message msg) {
            Toast.makeText(BugaGrpcActivity.this.getApplicationContext(), msg.obj.toString(), Toast.LENGTH_LONG).show();
        }
    };

    public class BugaEchoExecutor implements BugaRpcExecutor {
        @Keep
        @Override
        public MarshaledObject executeProcedure(String procedureName, MarshaledObject params) {
            int nChars = 20;
            String str = "Called " + procedureName + ": " + params.content.substring(0, Math.min(params.content.length(), nChars));
            Message msg = mHandler.obtainMessage(0, str);
            msg.sendToTarget();
            return params;
        }
    }

}
