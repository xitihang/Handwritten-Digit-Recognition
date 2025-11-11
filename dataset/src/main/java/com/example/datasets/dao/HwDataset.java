package com.example.datasets.dao;
import jakarta.persistence.*;
import lombok.Data;

@Entity
@Table(name = "dataset")
@Data
public class HwDataset {
    @Id
    @Column(name = "name")
    private String name;

    @Column(name = "numImages", nullable = false)
    private Long numImages;

    @Column(name = "address", nullable = false)
    private String address;

}
