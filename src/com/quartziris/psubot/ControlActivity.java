package com.quartziris.psubot;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.util.UUID;

import android.os.Bundle;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Intent;
import android.view.Menu;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

public class ControlActivity extends Activity {
   OutputStreamWriter cSwrOutput = null;
   InputStreamReader cSreInput = null;

	private static final int REQUEST_ENABLE_BT = 1;

   @Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_control);
		
		Button btnConnect = (Button)findViewById( R.id.btnConnect );
		EditText txtBTMAC = (EditText)findViewById( R.id.txtBTMAC );
		
		txtBTMAC.setText( "00:18:A1:12:0F:F9" );

	   btnConnect.setOnClickListener(
	      new View.OnClickListener() {
	         public void onClick( View view ) {
	            doConnect();
	         }
	      }
	   );
	}

	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
		// Inflate the menu; this adds items to the action bar if it is present.
		getMenuInflater().inflate(R.menu.activity_control, menu);
		return true;
	}

	protected void doConnect() {
	   EditText txtBTMAC = (EditText)findViewById( R.id.txtBTMAC );
	   BluetoothDevice devPSUBot;
	   BluetoothSocket btSocket;
	   InputStream stmInput = null;
	   OutputStream stmOutput = null;
      
      // Verify that Bluetooth is present and working.
      BluetoothAdapter btaBluetoothAdapter = 
         BluetoothAdapter.getDefaultAdapter();
      if( null == btaBluetoothAdapter ) {
         Toast.makeText( this, "Bluetooth is not available.",
              Toast.LENGTH_LONG ).show();
         finish();
         return;
      }
      
      // Verify that Bluetooth is turned on.
      if( !btaBluetoothAdapter.isEnabled() ) {
          Intent iteEnableBT = 
             new Intent( BluetoothAdapter.ACTION_REQUEST_ENABLE );
          startActivityForResult( iteEnableBT, REQUEST_ENABLE_BT );
          
          // TODO: Insist that we turn on Bluetooth or exit.
          //txtDisplayLog.append( "Bluetooth was not enabled.\n" );
          //return;
      }

      try {
         devPSUBot = btaBluetoothAdapter.getRemoteDevice( 
            txtBTMAC.getText().toString()
         );
         btSocket = devPSUBot.createRfcommSocketToServiceRecord(
            UUID.fromString( "00001101-0000-1000-8000-00805F9B34FB" )
         );
         btSocket.connect();
         
         Toast.makeText( this, "Connected.", Toast.LENGTH_LONG ).show();
         
         stmInput = btSocket.getInputStream();
         stmOutput = btSocket.getOutputStream();
         cSwrOutput = new OutputStreamWriter( stmOutput );
         cSreInput = new InputStreamReader( stmInput );
         
         Toast.makeText( this, "Streams opened.", Toast.LENGTH_LONG ).show();
         
         // DEBUG
         /* if( null != stmOutput && null != stmInput ) {
            cSwrOutput.write( "LED BLUE\r" );
            cSwrOutput.flush();
         } */
      } catch( Exception ex ) {
         /* btaBluetoothAdapter.getRemoteDevice() might throw an              * 
          * IllegalArgumentException if the BT address is invalid.            */
         /* An IOException might happen if the connection process fails.      */
         Toast.makeText( this, ex.getMessage(), Toast.LENGTH_LONG ).show();
      }
      
      //Log.v("EditText", txtBTMAC.getText().toString());
	}
}
