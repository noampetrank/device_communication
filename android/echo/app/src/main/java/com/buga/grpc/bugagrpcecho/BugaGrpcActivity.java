package com.buga.grpc.bugagrpcecho;

import android.content.Context;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.support.v7.app.AppCompatActivity;
import android.text.TextUtils;
import android.text.method.ScrollingMovementMethod;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import java.lang.ref.WeakReference;

public class BugaGrpcActivity extends AppCompatActivity {

    static {
        System.loadLibrary("buga_grpc");
    }

    private Button sendButton;
    private Button serverButton;
    private EditText hostEdit;
    private EditText portEdit;
    private EditText messageEdit;
    private EditText serverPortEdit;
    private TextView resultText;
    private GrpcTask grpcTask;
    private RunServerTask runServerTask;
    private Handler toastHandler;

    private int SERVER_START_SUCCEEDED = 1000;
    private int SERVER_START_FAILED = 1001;
    private int DEFAULT_PORT = 60004;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_buga_grpc);
        sendButton = (Button) findViewById(R.id.send_button);
        serverButton = (Button) findViewById(R.id.server_button);
        hostEdit = (EditText) findViewById(R.id.host_edit_text);
        portEdit = (EditText) findViewById(R.id.port_edit_text);
        messageEdit = (EditText) findViewById(R.id.message_edit_text);
        serverPortEdit = (EditText) findViewById(R.id.server_port_edit_text);
        serverPortEdit.setHint("Server port (default " + DEFAULT_PORT + ")");
        resultText = (TextView) findViewById(R.id.grpc_response_text);
        resultText.setMovementMethod(new ScrollingMovementMethod());
        toastHandler = new Handler(Looper.getMainLooper()) {
            @Override
            public void handleMessage(Message message) {
                if (message.what == SERVER_START_SUCCEEDED) {
                    // Control wouldn't reach this point because server.listen() is blocking.
//          Toast.makeText(BugaGrpcActivity.this, "Server started on port " + message.obj.toString(), Toast.LENGTH_LONG).show();
                } else if (message.what == SERVER_START_FAILED) {
                    if (runServerTask != null) {
                        runServerTask.cancel(true);
                        runServerTask = null;
                    }
                    serverButton.setText("Start gRPC Server");
                    Toast.makeText(BugaGrpcActivity.this, "Couldn't start server on port " + message.obj.toString(), Toast.LENGTH_LONG).show();
                }
            }
        };
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (runServerTask != null) {
            runServerTask.cancel(true);
            runServerTask = null;
            serverButton.setText("Start gRPC Server");
        }
        if (grpcTask != null) {
            grpcTask.cancel(true);
            grpcTask = null;
        }
    }

    public void sendMessage(View view) {
        ((InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE))
                .hideSoftInputFromWindow(hostEdit.getWindowToken(), 0);
        sendButton.setEnabled(false);
        resultText.setText("");
        grpcTask = new GrpcTask(this);
        grpcTask.executeOnExecutor(
                AsyncTask.THREAD_POOL_EXECUTOR,
                hostEdit.getText().toString(),
                messageEdit.getText().toString(),
                portEdit.getText().toString());
    }

    public void startOrStopServer(View view) {
        if (runServerTask != null) {
            runServerTask.cancel(true);
            runServerTask = null;
            serverButton.setText("Start gRPC Server");
            Toast.makeText(this, "Server stopped (actually not yet implemented...)", Toast.LENGTH_SHORT).show();
        } else {
            runServerTask = new RunServerTask(this);
            String portStr = serverPortEdit.getText().toString();
            int port = TextUtils.isEmpty(portStr) ? DEFAULT_PORT : Integer.valueOf(portStr);
            runServerTask.executeOnExecutor(AsyncTask.THREAD_POOL_EXECUTOR, port);
            serverButton.setText("Stop gRPC Server");
        }
    }

    private static class RunServerTask extends AsyncTask<Integer, Void, Void> {
        private final WeakReference<BugaGrpcActivity> activityReference;

        private RunServerTask(BugaGrpcActivity activity) {
            this.activityReference = new WeakReference<BugaGrpcActivity>(activity);
        }

        @Override
        protected Void doInBackground(Integer... params) {
            int port = params[0];
            BugaGrpcActivity activity = activityReference.get();
            if (activity != null) {
                boolean ret = activity.startServer(port);
                activity.toastHandler.obtainMessage(ret ? activity.SERVER_START_SUCCEEDED : activity.SERVER_START_FAILED, port).sendToTarget();
            }
            return null;
        }
    }

    private static class GrpcTask extends AsyncTask<String, Void, String> {
        private final WeakReference<BugaGrpcActivity> activityReference;

        private GrpcTask(BugaGrpcActivity activity) {
            this.activityReference = new WeakReference<BugaGrpcActivity>(activity);
        }

        @Override
        protected String doInBackground(String... params) {
            String host = params[0];
            String message = params[1];
            String portStr = params[2];
            int port = TextUtils.isEmpty(portStr) ? 50051 : Integer.valueOf(portStr);
            return sayHello(host, port, message);
        }

        @Override
        protected void onPostExecute(String result) {
            BugaGrpcActivity activity = activityReference.get();
            if (activity == null || isCancelled()) {
                return;
            }
            TextView resultText = (TextView) activity.findViewById(R.id.grpc_response_text);
            Button sendButton = (Button) activity.findViewById(R.id.send_button);
            resultText.setText(result);
            sendButton.setEnabled(true);
        }
    }

    /**
     * Invoked by native code to stop server when RunServerTask has been canceled, either by user
     * request or upon app moving to background.
     */
    public boolean isRunServerTaskCancelled() {
        if (runServerTask != null) {
            return runServerTask.isCancelled();
        }
        return false;
    }

    public static native String sayHello(String host, int port, String message);

    public native boolean startServer(int port);
}
