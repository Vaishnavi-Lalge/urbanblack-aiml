# Urban Black Backend Databases & Schemas

This document describes all the databases, schemas, and columns utilized across the microservices in the Urban Black backend.

## Service: `ride-service`

### Table: `ride_routes` (Entity: `RideRoute`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `RideRoute` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `rideId` | `String` | @Column(nullable = false) |
| `approachPolyline` | `String` | @Lob |
| `ridePolyline` | `String` | @Lob |
| `approachKm` | `Double` | - |
| `rideKm` | `Double` | - |

### Table: `rides` (Entity: `Ride`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Ride` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `userId` | `String` | @Column(nullable = false) |
| `driverId` | `String` | @Column |
| `pickupLat` | `Double` | @Column(nullable = false) |
| `pickupLng` | `Double` | @Column(nullable = false) |
| `dropLat` | `Double` | @Column(nullable = false) |
| `dropLng` | `Double` | @Column(nullable = false) |
| `pickupAddress` | `String` | - |
| `dropAddress` | `String` | - |
| `notes` | `String` | - |
| `vehicleType` | `String` | @Column |
| `status` | `RideStatus` | @Column(nullable = false) @Enumerated(EnumType.STRING) |
| `rideKm` | `Double` | - |
| `durationMin` | `Integer` | - |
| `fare` | `BigDecimal` | - |
| `requestedAt` | `LocalDateTime` | - |
| `startedAt` | `LocalDateTime` | - |
| `completedAt` | `LocalDateTime` | - |
| `createdAt` | `LocalDateTime` | - |
| `updatedAt` | `LocalDateTime` | - |
| `version` | `Long` | @Version |
| `nearbyDrivers` | `List<NearestDriverService.NearestDriverResult>` | @Transient |
| `userName` | `String` | @Transient |
| `userPhone` | `String` | @Transient |
| `otp` | `String` | @Column |

### Table: `reward_tree_nodes` (Entity: `RewardTreeNode`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `RewardTreeNode` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `nodeId` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `userId` | `Long` | @Column(nullable = false) |
| `parentNodeId` | `Long` | @Column(name = "parent_node_id") |
| `leftChildId` | `Long` | @Column(name = "left_child_id") |
| `rightChildId` | `Long` | @Column(name = "right_child_id") |
| `childrenCount` | `Integer` | @Column(name = "children_count") @Builder.Default |
| `depthLevel` | `Integer` | @Column(name = "depth_level") @Builder.Default |
| `bfsPosition` | `Long` | @Column(name = "bfs_position", unique = true, nullable = false) |
| `active` | `Boolean` | @Column(name = "active", nullable = false) @Builder.Default |
| `deactivatedAt` | `LocalDateTime` | @Column(name = "deactivated_at") |

### Table: `fare_config` (Entity: `FareConfig`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `FareConfig` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `perKmRate` | `BigDecimal` | @Column(nullable = false) |
| `minFare` | `BigDecimal` | @Column(nullable = false) |

### Table: `driver_locations` (Entity: `DriverLocation`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `DriverLocation` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `driverId` | `String` | @Column(nullable = false) |
| `lat` | `Double` | @Column(nullable = false) |
| `lng` | `Double` | @Column(nullable = false) |
| `bearing` | `Double` | - |
| `speedKmh` | `Double` | - |
| `updatedAt` | `LocalDateTime` | @Column(nullable = false) |

### Table: `driver_shifts` (Entity: `DriverShift`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `DriverShift` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `driverId` | `String` | @Column(nullable = false) |
| `shiftRef` | `String` | @Column(name = "shift_ref", unique = true) |
| `shiftStart` | `LocalDateTime` | @Column(nullable = false) |
| `shiftEnd` | `LocalDateTime` | - |
| `status` | `DriverStatus` | @Column(nullable = false) @Enumerated(EnumType.STRING) |
| `goalKm` | `Double` | @Column(name = "goal_km", nullable = false) |
| `goalKmReached` | `Double` | @Column(name = "goal_km_reached", nullable = false) |
| `totalRideKm` | `Double` | @Column(nullable = false) |
| `totalDeadKm` | `Double` | @Column(nullable = false) |
| `totalFreeRoamingKm` | `Double` | @Column(nullable = false) |
| `totalKm` | `Double` | @Column(nullable = false) |

### Table: `driver_km_log` (Entity: `DriverKmLog`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `DriverKmLog` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `driverId` | `String` | @Column(nullable = false) |
| `shiftId` | `String` | @Column(nullable = false) |
| `category` | `KmCategory` | @Column(nullable = false) @Enumerated(EnumType.STRING) |
| `km` | `Double` | @Column(nullable = false) |
| `rideId` | `String` | - |
| `recordedAt` | `LocalDateTime` | @Column(nullable = false) |

### Table: `driver_km_ledger` (Entity: `DriverKmLedger`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `DriverKmLedger` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `driverId` | `String` | @Column(nullable = false) |
| `date` | `LocalDate` | @Column(nullable = false) |
| `rideKm` | `Double` | @Column(nullable = false) |
| `deadKm` | `Double` | @Column(nullable = false) |
| `freeRoamingKm` | `Double` | @Column(nullable = false) |
| `totalKm` | `Double` | @Column(nullable = false) |
| `quotaKm` | `Double` | @Column(nullable = false) |
| `overuseKm` | `Double` | @Column(nullable = false) |
| `tomorrowQuota` | `Double` | @Column(nullable = false) |

## Service: `cab-registeration-service`

### Table: `cab_application` (Entity: `CabApplication`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `CabApplication` | `class` | @Builder @NoArgsConstructor @AllArgsConstructor @Table(name = "cab_application") @Data |
| `cabApplicationId` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `username` | `String` | - |
| `numberPlate` | `String` | - |
| `rcNumber` | `RcDetails` | @JoinColumn(name = "rc_number_id") @OneToOne(cascade = CascadeType.ALL) |
| `carName` | `String` | - |
| `cabModel` | `CabModel` | @Enumerated(EnumType.STRING) |
| `category` | `CabCategory` | @Enumerated(EnumType.STRING) |
| `acType` | `String` | - |
| `vehicleYear` | `Integer` | - |
| `kms` | `Long` | - |
| `passingDate` | `String` | - |
| `fuelType` | `String` | - |
| `packageAmount` | `BigDecimal` | - |
| `status` | `ApplicationStatus` | @Enumerated(EnumType.STRING) |
| `stage` | `ApplicationStage` | @Enumerated(EnumType.STRING) |
| `createdDate` | `LocalDateTime` | @CreationTimestamp |

### Table: `RC_Details` (Entity: `RcDetails`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `RcDetails` | `class` | @Table(name = "RC_Details") @NoArgsConstructor @AllArgsConstructor @Data @Entity |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `rcNumber` | `String` | - |
| `fitUpToDate` | `String` | - |
| `registrationDate` | `String` | - |
| `ownerName` | `String` | - |
| `vehicleChasiNumber` | `String` | - |
| `vehicleEngineNumber` | `String` | - |
| `vehicleModel` | `CabModel` | @Enumerated(EnumType.STRING) |
| `fuelType` | `String` | - |
| `insuranceCompanyName` | `String` | - |
| `insurancePolicyNumber` | `String` | - |
| `insuranceUptoDate` | `String` | - |
| `rcStatus` | `String` | - |
| `challanDetails` | `String` | @Column(columnDefinition = "TEXT") |
| `otherDetails` | `String` | @Column(columnDefinition = "TEXT") |

### Table: `vendor_package` (Entity: `VendorPackage`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `VendorPackage` | `class` | @Builder @NoArgsConstructor @AllArgsConstructor @Table(name = "vendor_package") @Data |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `monthlyPackage` | `BigDecimal` | - |
| `monthlyKm` | `Double` | - |
| `dailyHours` | `Double` | - |
| `monthlyDaysCover` | `Integer` | - |
| `perDayKm` | `Double` | - |
| `vendorPerDayPackage` | `BigDecimal` | - |

## Service: `auth-service`

### Table: `admin_details` (Entity: `AuthUser`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `AuthUser` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `name` | `String` | - |
| `email` | `String` | @Column(nullable = true) |
| `mobile` | `String` | @Column(nullable = false) |
| `password` | `String` | @Column(nullable = true) |
| `role` | `Role` | @Column(nullable = false) @Enumerated(EnumType.STRING) |
| `enabled` | `boolean` | - |

### Table: `otp_records` (Entity: `Otp`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Otp` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `mobileNumber` | `String` | @Column(nullable = false, unique = true) |
| `otpValue` | `String` | @Column(nullable = false) |
| `expirationTime` | `LocalDateTime` | @Column(nullable = false) |

## Service: `fleet-service`

### Table: `vehicle_assignment` (Entity: `VehicleAssignment`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `VehicleAssignment` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "vehicle_assignment") |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `driverId` | `String` | - |
| `vehicle` | `Vehicle` | @JoinColumn(name = "vehicle_id") @ManyToOne |
| `startKm` | `Integer` | - |
| `endKm` | `Integer` | - |
| `startFuel` | `Integer` | - |
| `endFuel` | `Integer` | - |
| `startPhotos` | `String` | @Column(columnDefinition = "TEXT") |
| `endPhotos` | `String` | @Column(columnDefinition = "TEXT") |
| `inspectionChecklist` | `String` | @Column(columnDefinition = "TEXT") |
| `damages` | `String` | @Column(columnDefinition = "TEXT") |
| `startTime` | `LocalDateTime` | - |
| `endTime` | `LocalDateTime` | - |
| `status` | `String` | - |

### Table: `Vehicle` (Entity: `Vehicle`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Vehicle` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Data @Entity |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `vehicleNumber` | `String` | - |
| `model` | `String` | - |
| `make` | `String` | - |
| `year` | `Integer` | - |
| `fuelType` | `String` | - |
| `capacity` | `Integer` | - |
| `currentKm` | `Integer` | - |
| `lastServiceDate` | `LocalDate` | - |
| `nextServiceDate` | `LocalDate` | - |
| `insuranceExpiry` | `LocalDate` | - |
| `status` | `String` | - |

### Table: `issue_report` (Entity: `IssueReport`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `IssueReport` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "issue_report") |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `category` | `IssueCategory` | @Enumerated(EnumType.STRING) |
| `severity` | `IssueSeverity` | @Enumerated(EnumType.STRING) |
| `title` | `String` | - |
| `description` | `String` | @Column(columnDefinition = "TEXT") |
| `locationAddress` | `String` | - |
| `latitude` | `Double` | - |
| `longitude` | `Double` | - |
| `photos` | `String` | @Column(columnDefinition = "TEXT") |
| `vehicleId` | `String` | - |
| `tripId` | `String` | - |
| `driverId` | `String` | - |
| `timestamp` | `LocalDateTime` | - |
| `status` | `IssueStatus` | @Enumerated(EnumType.STRING) |
| `ticketNumber` | `String` | - |

### Table: `fuel_entry` (Entity: `FuelEntry`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `FuelEntry` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "fuel_entry") |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `vehicle` | `Vehicle` | @JoinColumn(name = "vehicle_id") @ManyToOne |
| `tripId` | `String` | - |
| `fuelType` | `FuelType` | @Enumerated(EnumType.STRING) |
| `quantity` | `Double` | - |
| `amount` | `Double` | - |
| `odometerReading` | `Integer` | - |
| `stationName` | `String` | - |
| `stationAddress` | `String` | - |
| `latitude` | `Double` | - |
| `longitude` | `Double` | - |
| `receiptImage` | `String` | @Column(columnDefinition = "TEXT") |
| `timestamp` | `LocalDateTime` | - |
| `status` | `String` | - |
| `driverId` | `String` | - |

## Service: `trafficOperation-service`

### Table: `users` (Entity: `User`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `User` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `username` | `String` | - |
| `email` | `String` | - |
| `role` | `Role` | @JsonIgnore @JoinColumn(name = "role_id") @ManyToOne |

### Table: `shift_master` (Entity: `ShiftMaster`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `ShiftMaster` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `shiftName` | `String` | @Column(nullable = false, length = 50) |
| `startTime` | `LocalTime` | @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "HH:mm:ss") @Column(nullable = false) |
| `endTime` | `LocalTime` | @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "HH:mm:ss") @Column(nullable = false) |
| `isActive` | `Boolean` | @Builder.Default |
| `createdAt` | `LocalDateTime` | @Column(name = "created_at", updatable = false) |

### Table: `roles` (Entity: `Role`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Role` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `roleName` | `String` | @Column(unique = true, nullable = false) |

### Table: `stage_patti` (Entity: `FareSlab`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `FareSlab` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `stageId` | `Integer` | @Column(nullable = false) |
| `minDistance` | `Double` | @Column(nullable = false) |
| `maxDistance` | `Double` | @Column(nullable = false) |
| `nonAcFare` | `Double` | @Column(nullable = false) |
| `acPercentage` | `Double` | @Column(nullable = false) |
| `isActive` | `Boolean` | - |

### Table: `driver_daily_assignment` (Entity: `DriverDailyAssignment`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `DriverDailyAssignment` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `assignmentId` | `Long` | @Column(name = "assignment_id") @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `assignmentDate` | `LocalDate` | @Column(name = "assignment_date", nullable = false) |
| `driverId` | `Long` | @Column(name = "driver_id", nullable = false) |
| `cabId` | `Long` | @Column(name = "cab_id", nullable = false) |
| `shift` | `ShiftMaster` | @JoinColumn(name = "shift_id", nullable = false) @ManyToOne |
| `centerPoint` | `CenterPoint` | @JoinColumn(name = "center_point_id", nullable = false) @ManyToOne |
| `depot` | `Depot` | @JoinColumn(name = "depot_id", nullable = false) @ManyToOne |
| `status` | `String` | @Column(name = "status", length = 20) |
| `createdBy` | `String` | @Column(name = "created_by") |
| `createdAt` | `LocalDateTime` | @Column(name = "created_at", updatable = false) |

### Table: `center_points` (Entity: `CenterPoint`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `CenterPoint` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `pointName` | `String` | - |
| `latitude` | `Double` | - |
| `longitude` | `Double` | - |
| `depot` | `Depot` | @JsonIgnore @JoinColumn(name = "depot_id") @ManyToOne |
| `depotId` | `Long` | @Column(name = "depot_id", insertable = false, updatable = false) |

### Table: `depots` (Entity: `Depot`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Depot` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `depotCode` | `String` | @Column(unique = true, nullable = false) |
| `depotName` | `String` | - |
| `city` | `String` | - |
| `fullAddress` | `String` | - |
| `latitude` | `Double` | - |
| `longitude` | `Double` | - |
| `zone` | `String` | - |
| `capacity` | `Integer` | - |
| `operatingStart` | `LocalTime` | @com.fasterxml.jackson.annotation.JsonFormat(pattern = "HH:mm:ss") |
| `operatingEnd` | `LocalTime` | @com.fasterxml.jackson.annotation.JsonFormat(pattern = "HH:mm:ss") |
| `registrationDate` | `LocalDate` | @com.fasterxml.jackson.annotation.JsonFormat(pattern = "yyyy-MM-dd") |
| `isActive` | `Boolean` | @Builder.Default |
| `centerPoints` | `List<CenterPoint>` | @JsonIgnore @OneToMany(mappedBy = "depot", cascade = CascadeType.ALL) |

### Table: `assign_manager` (Entity: `AssignManager`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `AssignManager` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @Column(name = "assign_manager_to_depot_id") @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `registrationDate` | `LocalDate` | @Column(name = "registration_date", nullable = false) |
| `managerId` | `Long` | @Column(name = "manager_id", nullable = false) |
| `depotId` | `Long` | @Column(name = "depot_id", nullable = false) |

### Table: `allocate_vehicles` (Entity: `AllocationVehicle`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `AllocationVehicle` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @Column(name = "vehicle_to_depot_id") @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `depotId` | `Long` | @Column(name = "depot_id") |
| `registrationDate` | `LocalDate` | @Column(name = "registration_date") |
| `vehiclesCount` | `Integer` | @Column(name = "vehicles_count") |
| `vehicleIdsRaw` | `String` | @Column(name = "vehicle_ids", columnDefinition = "TEXT") |

### Table: `assign_driver` (Entity: `AllocationDriver`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `AllocationDriver` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @Column(name = "assign_drivers_to_depot_id") @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `depotId` | `Long` | @Column(name = "depot_id") |
| `registrationDate` | `LocalDate` | @Column(name = "registration_date") |
| `driversCount` | `Integer` | @Column(name = "drivers_count") |
| `employeeIdsRaw` | `String` | @Column(name = "employee_ids", columnDefinition = "TEXT") |

### Table: `t2` (Entity: `T2`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `T2` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `subCenterId` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `subCenterName` | `String` | @Column(nullable = false) |
| `location` | `String` | @Column(nullable = false) |
| `latitude` | `Double` | @Column(nullable = false) |
| `longitude` | `Double` | @Column(nullable = false) |
| `status` | `String` | @Column(nullable = false) |
| `depotId` | `Long` | @Column(nullable = false) |
| `inspectorId` | `Long` | @Column(nullable = false) |
| `isDeleted` | `Boolean` | - |

## Service: `EmployeeDetails-Service`

### Table: `aadhaar_details` (Entity: `Aadhaar`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Aadhaar` | `class` | @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "aadhaar_details") @Entity |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `aadhaarNumber` | `String` | @Column(nullable = false, unique = true, length = 20) |
| `dateOfBirth` | `LocalDate` | - |
| `zip` | `String` | - |
| `fullName` | `String` | - |
| `gender` | `String` | - |
| `address` | `AadhaarAddress` | @Embedded |
| `clientId` | `String` | @Column(unique = true) |
| `profileImage` | `String` | @Lob |
| `zipData` | `String` | @Lob |
| `rawXml` | `String` | @Lob |
| `shareCode` | `String` | - |
| `careOf` | `String` | - |
| `verifiedAt` | `LocalDateTime` | - |
| `createdAt` | `LocalDateTime` | - |
| `updatedAt` | `LocalDateTime` | - |
| `employee` | `Employee` | @JsonIgnore @JoinColumn(name = "employee_id") @OneToOne |

### Table: `driving_license` (Entity: `DrivingLicense`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `DrivingLicense` | `class` | @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "driving_license") @Entity |
| `recordId` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `licenseNumber` | `String` | - |
| `name` | `String` | - |
| `permanentAddress` | `String` | - |
| `permanentZip` | `String` | - |
| `licenseType` | `String` | - |
| `fatherOrHusbandName` | `String` | - |
| `licenseExpiryDate` | `LocalDate` | - |
| `transportIssueDate` | `LocalDate` | - |
| `transportExpiryDate` | `LocalDate` | - |
| `vehicleClasses` | `String` | - |
| `otherDetails` | `String` | @Column(columnDefinition = "TEXT") |
| `employee` | `Employee` | @JsonIgnore @JoinColumn(name = "employee_id") @OneToOne |

### Table: `employees` (Entity: `Employee`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Employee` | `class` | @Schema(description = "Employee entity — represents an onboarded Urban Black employee") @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "employees") |
| `id` | `Long` | @Schema(description = "Auto-generated employee ID", example = "1") @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `userId` | `Long` | @Schema(description = "Linked user ID from user-service", example = "101") |
| `fullName` | `String` | @JsonAlias({"employeeName", "fullName"}) @Schema(description = "Full legal name of the employee", example = "Rajesh Kumar") @Column(nullable = false) |
| `email` | `String` | @Schema(description = "Official email address", example = "rajesh.kumar@urbanblack.com") @Column(nullable = false, unique = true) |
| `mobile` | `String` | @JsonAlias({"mobileNo", "mobile"}) @Schema(description = "Mobile number", example = "9876543210") @Column(nullable = false, unique = true) |
| `role` | `EmployeeRole` | @JsonAlias({"employeeRole", "role"}) |
| `accountStatus` | `AccountStatus` | @Schema(description = "Account status", example = "ACTIVE") @Column(nullable = false) @Enumerated(EnumType.STRING) |
| `verificationStatus` | `com.urbanblack.common.enums.VerificationStatus` | @Schema(description = "Verification status of employee documents", example = "PENDING_VERIFICATION") @Column @Enumerated(EnumType.STRING) |
| `registrationDate` | `java.time.LocalDate` | @Schema(description = "Date when the employee was registered", example = "2024-03-06") @Column |
| `experience` | `String` | @Schema(description = "Years of experience", example = "5") @Column |
| `dateOfBirth` | `java.time.LocalDate` | @Schema(description = "Date of Birth", example = "1990-01-01") @Column |
| `pincode` | `String` | @Schema(description = "Pin Code", example = "411038") @Column |
| `medicalInsuranceNumber` | `String` | @Schema(description = "Medical Insurance Number", example = "MED123456") @Column |
| `username` | `String` | @Schema(description = "Auto-generated username for employee login", example = "rajesh.kumar@urbanblack.in") @Column |
| `tempPassword` | `String` | @Schema(description = "Auto-generated temporary password (sent via email)", example = "UB@48392") @Column |
| `credentialsSent` | `boolean` | @Schema(description = "True once credentials have been emailed to the employee", example = "false") @Column(nullable = false, columnDefinition = "BOOLEAN DEFAULT FALSE") |
| `aadhaar` | `Aadhaar` | @OneToOne(mappedBy = "employee", cascade = CascadeType.ALL) |
| `drivingLicense` | `DrivingLicense` | @OneToOne(mappedBy = "employee", cascade = CascadeType.ALL) |
| `education` | `EmployeeEducation` | @OneToOne(mappedBy = "employee", cascade = CascadeType.ALL) |
| `bankDetails` | `BankDetails` | @OneToOne(mappedBy = "employee", cascade = CascadeType.ALL) |

### Table: `employee_education` (Entity: `EmployeeEducation`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `EmployeeEducation` | `class` | @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "employee_education") @Entity |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `highestQualification` | `String` | - |
| `university` | `String` | - |
| `passingYear` | `String` | - |
| `percentage` | `String` | - |
| `employee` | `Employee` | @JsonIgnore @JoinColumn(name = "employee_id") @OneToOne |

### Table: `employee_package` (Entity: `EmployeePackage`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `EmployeePackage` | `class` | @Builder @NoArgsConstructor @AllArgsConstructor @Table(name = "employee_package") @Data |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `designation` | `String` | - |
| `durationMonths` | `Integer` | - |
| `inHandSalary` | `Double` | - |
| `monthlyOff` | `Integer` | - |

### Table: `bank_details` (Entity: `BankDetails`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `BankDetails` | `class` | @AllArgsConstructor @NoArgsConstructor @Data @Table(name = "bank_details") @Entity |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `accountHolderName` | `String` | - |
| `accountNumber` | `String` | - |
| `bankName` | `String` | - |
| `branchName` | `String` | - |
| `ifscCode` | `String` | - |
| `employee` | `Employee` | @JsonIgnore @JoinColumn(name = "employee_id") @OneToOne |

## Service: `user-service`

### Table: `users` (Entity: `User`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `User` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @Id |
| `name` | `String` | @Column(nullable = false) |
| `email` | `String` | @Column(unique = true, nullable = false, updatable = false) |
| `phone` | `String` | @Column(unique = true, nullable = false) |
| `active` | `Boolean` | @Builder.Default @Column(nullable = false) |
| `createdAt` | `LocalDateTime` | @Column(updatable = false) @CreationTimestamp |
| `updatedAt` | `LocalDateTime` | @UpdateTimestamp |

## Service: `wallet-service`

### Table: `wallets` (Entity: `Wallet`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Wallet` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `userId` | `Long` | @Column(nullable = false, unique = true) |
| `balance` | `BigDecimal` | @Builder.Default @Column(precision = 12, scale = 2) |
| `totalEarned` | `BigDecimal` | @Builder.Default @Column(precision = 12, scale = 2) |

### Table: `reward_transactions` (Entity: `RewardTransaction`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `RewardTransaction` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `triggeringNode` | `Long` | - |
| `beneficiaryNode` | `Long` | - |
| `beneficiaryUser` | `Long` | - |
| `uplineLevel` | `Integer` | - |
| `amount` | `BigDecimal` | @Column(precision = 10, scale = 2) |

### Table: `admin_wallet` (Entity: `AdminWallet`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `AdminWallet` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `balance` | `BigDecimal` | @Builder.Default @Column(precision = 12, scale = 2) |

### Table: `admin_transactions` (Entity: `AdminTransaction`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `AdminTransaction` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `triggeringNode` | `Long` | - |
| `amount` | `BigDecimal` | @Column(precision = 10, scale = 2, nullable = false) |

## Service: `notification-service`

### Table: `notification_logs` (Entity: `NotificationLog`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `NotificationLog` | `class` | @AllArgsConstructor @NoArgsConstructor @Builder @Data @Table(name = "notification_logs") |
| `id` | `Long` | @GeneratedValue(strategy = GenerationType.IDENTITY) @Id |
| `recipientEmail` | `String` | @Column(nullable = false) |
| `recipientName` | `String` | - |
| `subject` | `String` | @Column(nullable = false) |
| `type` | `NotificationType` | @Column(nullable = false) @Enumerated(EnumType.STRING) |
| `status` | `NotificationStatus` | @Column(nullable = false) @Enumerated(EnumType.STRING) |
| `sourceService` | `String` | - |
| `referenceId` | `String` | - |
| `errorMessage` | `String` | @Column(columnDefinition = "TEXT") |
| `retryCount` | `int` | @Builder.Default @Column(nullable = false) |
| `updatedAt` | `LocalDateTime` | - |

## Service: `driver-service`

### Table: `Driver` (Entity: `Driver`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Driver` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `email` | `String` | @Column(unique = true, nullable = false) |
| `phoneNumber` | `String` | @Column(name = "phone_number", unique = true) |
| `firstName` | `String` | - |
| `lastName` | `String` | - |
| `profileImage` | `String` | - |
| `isActive` | `boolean` | - |
| `isVerified` | `boolean` | - |
| `city` | `String` | - |
| `language` | `String` | - |
| `employeeId` | `String` | - |
| `depotName` | `String` | - |
| `licenseNumber` | `String` | - |
| `rating` | `Double` | - |
| `totalTrips` | `Integer` | - |
| `totalDistance` | `Double` | - |
| `status` | `DriverStatus` | @Enumerated(EnumType.STRING) |
| `dateOfJoining` | `LocalDate` | - |
| `createdAt` | `LocalDateTime` | - |
| `updatedAt` | `LocalDateTime` | - |

### Table: `shifts` (Entity: `Shift`)
| Column Name | Type | Attributes/Usage |
|-------------|------|------------------|
| `Shift` | `class` | @Builder @AllArgsConstructor @NoArgsConstructor @Setter @Getter |
| `id` | `String` | @GeneratedValue(strategy = GenerationType.UUID) @Id |
| `driverId` | `String` | - |
| `status` | `ShiftStatus` | @Enumerated(EnumType.STRING) |
| `availability` | `DriverAvailability` | @Enumerated(EnumType.STRING) |
| `clockInTime` | `LocalDateTime` | - |
| `clockInLatitude` | `Double` | @Column(name = "clock_in_latitude") |
| `clockInLongitude` | `Double` | @Column(name = "clock_in_longitude") |
| `clockOutTime` | `LocalDateTime` | - |
| `clockOutLatitude` | `Double` | @Column(name = "clock_out_latitude") |
| `clockOutLongitude` | `Double` | @Column(name = "clock_out_longitude") |
| `lastOnlineEpochSecond` | `Long` | @Transient |
| `lastOnlineTime` | `LocalDateTime` | @Column(name = "last_online_time") |
| `lastOfflineTime` | `LocalDateTime` | @Column(name = "last_offline_time") |
| `accumulatedActiveSeconds` | `long` | - |
| `totalActiveMinutes` | `long` | - |
| `startingOdometer` | `Integer` | - |
| `fuelLevelAtStart` | `FuelLevel` | @Enumerated(EnumType.STRING) |
| `endingOdometer` | `Integer` | - |
| `fuelLevelAtEnd` | `FuelLevel` | @Enumerated(EnumType.STRING) |
| `vehicleCondition` | `VehicleCondition` | @Enumerated(EnumType.STRING) |

