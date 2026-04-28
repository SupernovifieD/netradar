export interface ServiceCheck {
  id: number;
  timestamp: string;
  service: string;
  latency: string;
  packet_loss: string;
  dns: string;
  tcp: string;
  status: string;
}
