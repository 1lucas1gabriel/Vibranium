/**************************************************************************
 * BLE_USART library
 * Lucas Gabriel Cosmo Morais
 * 11/2020
 **************************************************************************/
#ifndef BLE_USART_H
#define BLE_USART_H

#include <libopencm3/stm32/usart.h>

#define SCALE_2G		'0'
#define SCALE_4G		'1'
#define SCALE_8G		'2'
#define SCALE_16G		'3'
#define TIMER_5s		'A'
#define TIMER_10s		'B'
#define TIMER_5m		'C'
#define TIMER_10m		'D'

// Config options
extern const char sens[4];
extern const char timers[4];

bool ble_connected(void);
bool ble_recv_cmd(char data);
bool ble_recv_cmds(const char* cmds_list, uint8_t cmds_list_size);
bool ble_recv_config(void);

typedef struct{
	
	char sensitivity;
	char alarm_timer;
}DevConfigStruct;


extern volatile uint8_t		usart_rx_data;
extern volatile bool 		flag_read_usart;
extern DevConfigStruct 		devconfig;

#endif	// BLE_USART_H 
