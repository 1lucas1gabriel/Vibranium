/**************************************************************************
 * BLE_USART library
 * Lucas Gabriel Cosmo Morais
 * 11/2020
 **************************************************************************/

#include "ble_usart.h"

volatile uint8_t	usart_rx_data;
volatile bool		flag_read_usart = false;

// Config command options
const char sens[] = {SCALE_2G, SCALE_4G, SCALE_8G, SCALE_16G};

const char timers[] = {TIMER_5s, TIMER_10s, TIMER_5m, TIMER_10m};

// Config setup by user (default config)
DevConfigStruct devconfig = {SCALE_2G, TIMER_5s};


/**************************************************************************
 * GET BLE CONNECTED
 **************************************************************************/
bool ble_connected(void){
	
	// recv '(C)onnected' from usart/user	
	return ble_recv_cmd('C');
}


/**************************************************************************
 * BLOCK PROGRAM AND WAIT FOR RECV COMMAND
 **************************************************************************/
bool ble_recv_cmd(char cmd){
	
	while(1){
		if(flag_read_usart){
			flag_read_usart = false;
			
			// recv 'cmd' from usart/user
			if(usart_rx_data == cmd)				
				break;
		}
	}
	return true;
}


/**************************************************************************
 * BLOCK PROGRAM AND WAIT FOR RECV ANY OF SPECIFIED COMMAND
 **************************************************************************/
bool ble_recv_cmds(const char* cmds_list, uint8_t cmds_list_size){
	
	uint8_t i = 0;
	bool match = false;

	while(1){
		if(flag_read_usart){
			flag_read_usart = false;
			
			// -----------------------------------------------------//
			// check if we recv any of spcfied cmds from usart/user //
			// If we recv, this function unblocks 			//
			// You can read usart_rx_data to obtain that cmd	//
			// -----------------------------------------------------//
			while(i < cmds_list_size){			
				if(usart_rx_data == cmds_list[i]){				
					match = true;
					break;
				}
				++i;
			}
			// return index to initial position to a next comparison 
			i = 0;
		}
		if(match == true)
			break;
	}
	return true;
}


/**************************************************************************
 * WAIT AND SET USER CONFIGURATION
 **************************************************************************/
bool ble_recv_config(void){

	char config_mode = 's';
	bool exit_config = false;

	while(1){

		switch(config_mode){
			
			// '(s)ensibility' config
			case 's':
				while(!ble_recv_cmds(sens, sizeof(sens)));
				devconfig.sensitivity = usart_rx_data;							
				config_mode = 't';
				break;

			// 'alarm (t)imer' config
			case 't':
				while(!ble_recv_cmds(timers, sizeof(timers)));
				devconfig.alarm_timer = usart_rx_data;	
				config_mode = 'o';
				break;

			// 'config (o)k'
			case 'o': 
				exit_config = true;
				break;
		}
		
		// finished configuration
		if(exit_config == true)
			break;		
	}

	return true;
}
