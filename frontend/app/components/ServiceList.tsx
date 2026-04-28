"use client"

import { useEffect, useState } from "react"
import ServiceCard from "./ServiceCard"
import { getServiceBuckets } from "@/lib/api"

export default function ServiceList({ initialServices }) {

  const [services, setServices] = useState(initialServices)

  async function refresh() {
    const data = await getServiceBuckets()
    setServices(data)
  }

  useEffect(() => {

    const interval = setInterval(() => {
      refresh()
    }, 60000)

    return () => clearInterval(interval)

  }, [])

  return (
    <>
      {services.map(s => (
        <ServiceCard
          key={s.service}
          name={s.service}
          buckets={s.buckets}
        />
      ))}
    </>
  )
}
