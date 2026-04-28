import Header from "./components/Header";
import Footer from "./components/Footer";
import ServiceList from "./components/ServiceList";
import { getServiceBuckets } from "@/lib/api";

export default async function Home() {

  const services = await getServiceBuckets();

  return (
    <main className="container">

      <Header/>

      <hr/>

      <ServiceList initialServices={services} />

      <Footer/>

    </main>
  );
}
