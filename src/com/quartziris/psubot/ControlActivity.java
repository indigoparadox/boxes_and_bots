package com.quartziris.psubot;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.util.HashMap;
import java.util.UUID;

import android.os.Bundle;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Intent;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

public class ControlActivity extends Activity {
   protected BluetoothSocket cBtSocket = null;
   protected OutputStreamWriter cSwrOutput = null;
   protected InputStreamReader cSreInput = null;
   
   protected HashMap<Integer,String> cMapKeysDown = new HashMap<Integer,String>();
   protected HashMap<Integer,String> cMapKeysUp = new HashMap<Integer,String>();

	private static final int REQUEST_ENABLE_BT = 1;

   @Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_control);
		
		// LED keys.
		cMapKeysDown.put( KeyEvent.KEYCODE_J, "LED RED\r" );
		cMapKeysDown.put( KeyEvent.KEYCODE_K, "LED GREEN\r" );
		cMapKeysDown.put( KeyEvent.KEYCODE_L, "LED BLUE\r" );
		
		// Driving keys.
		cMapKeysDown.put( KeyEvent.KEYCODE_W, "DRIVE F\r" );
		cMapKeysUp.put( KeyEvent.KEYCODE_W, "DRIVE S\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_A, "DRIVE L\r" );
      cMapKeysUp.put( KeyEvent.KEYCODE_A, "DRIVE S\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_S, "DRIVE B\r" );
      cMapKeysUp.put( KeyEvent.KEYCODE_S, "DRIVE S\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_D, "DRIVE R\r" );
      cMapKeysUp.put( KeyEvent.KEYCODE_D, "DRIVE S\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_Q, "DRIVE PL\r" );
      cMapKeysUp.put( KeyEvent.KEYCODE_Q, "DRIVE S\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_E, "DRIVE PR\r" );
      cMapKeysUp.put( KeyEvent.KEYCODE_E, "DRIVE S\r" );
      
      // Eye keys.
      cMapKeysDown.put( KeyEvent.KEYCODE_Z, "EYE L\r" );
      cMapKeysUp.put( KeyEvent.KEYCODE_Z, "EYE S\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_C, "EYE R\r" );
      cMapKeysUp.put( KeyEvent.KEYCODE_C, "EYE S\r" );
      
      // Beep keys.
      cMapKeysDown.put( KeyEvent.KEYCODE_B, "BEEP 76 100\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_N, "BEEP 67 100\r" );
      cMapKeysDown.put( KeyEvent.KEYCODE_M, "BEEP 60 100\r" );
		
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
	
   @Override
   protected void onPause() {
      super.onPause();
      
      try {
         if( null != cBtSocket ) {
            cBtSocket.close();
         }
      } catch( IOException ex ) {
         Toast.makeText( this, ex.getMessage(), Toast.LENGTH_LONG ).show();
      }
   }

	@Override
   public boolean onKeyDown( int keyCode, KeyEvent event ) {
      //Toast.makeText( this, "KeyDown", Toast.LENGTH_LONG ).show();
      
      if( 
         null != cSwrOutput && cMapKeysDown.containsKey( keyCode ) 
      ) {
         try {
            cSwrOutput.write( cMapKeysDown.get( keyCode ) );
            cSwrOutput.flush();
            //Toast.makeText( this, "Sent!", Toast.LENGTH_SHORT ).show();
         } catch( IOException ex ) {
            Toast.makeText( this, ex.getMessage(), Toast.LENGTH_LONG ).show();
         }
      }
      
      return super.onKeyDown( keyCode, event );
   }

   @Override
   public boolean onKeyUp( int keyCode, KeyEvent event ) {
      //Toast.makeText( this, "KeyUp", Toast.LENGTH_LONG ).show();

      if( 
         null != cSwrOutput && cMapKeysUp.containsKey( keyCode ) 
      ) {
         try {
            cSwrOutput.write( cMapKeysUp.get( keyCode ) );
            cSwrOutput.flush();
            //Toast.makeText( this, "Sent!", Toast.LENGTH_SHORT ).show();
         } catch( IOException ex ) {
            Toast.makeText( this, ex.getMessage(), Toast.LENGTH_LONG ).show();
         }
      }
      
      return super.onKeyUp( keyCode, event );
   }

   protected void doConnect() {
	   EditText txtBTMAC = (EditText)findViewById( R.id.txtBTMAC );
	   BluetoothDevice devPSUBot;
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
         cBtSocket = devPSUBot.createRfcommSocketToServiceRecord(
            UUID.fromString( "00001101-0000-1000-8000-00805F9B34FB" )
         );
         cBtSocket.connect();
         
         Toast.makeText( this, "Connected.", Toast.LENGTH_LONG ).show();
         
         stmInput = cBtSocket.getInputStream();
         stmOutput = cBtSocket.getOutputStream();
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
