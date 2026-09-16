package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000*\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0004\n\u0002\u0010\t\n\u0002\b\u0014\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B=\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0003\u0012\b\b\u0001\u0010\u0005\u001a\u00020\u0003\u0012\u0006\u0010\u0006\u001a\u00020\u0003\u0012\b\b\u0001\u0010\u0007\u001a\u00020\b\u0012\b\u0010\t\u001a\u0004\u0018\u00010\u0001¢\u0006\u0004\b\n\u0010\u000bJ\t\u0010\u0015\u001a\u00020\u0003HÆ\u0003J\t\u0010\u0016\u001a\u00020\u0003HÆ\u0003J\t\u0010\u0017\u001a\u00020\u0003HÆ\u0003J\t\u0010\u0018\u001a\u00020\u0003HÆ\u0003J\t\u0010\u0019\u001a\u00020\bHÆ\u0003J\u000b\u0010\u001a\u001a\u0004\u0018\u00010\u0001HÆ\u0003JG\u0010\u001b\u001a\u00020\u00002\b\b\u0002\u0010\u0002\u001a\u00020\u00032\b\b\u0002\u0010\u0004\u001a\u00020\u00032\b\b\u0003\u0010\u0005\u001a\u00020\u00032\b\b\u0002\u0010\u0006\u001a\u00020\u00032\b\b\u0003\u0010\u0007\u001a\u00020\b2\n\b\u0002\u0010\t\u001a\u0004\u0018\u00010\u0001HÆ\u0001J\u0014\u0010\u001c\u001a\u00020\u001d2\b\u0010\u001e\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u001f\u001a\u00020 HÖ\u0081\u0004J\n\u0010!\u001a\u00020\u0003HÖ\u0081\u0004R\u0011\u0010\u0002\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\rR\u0011\u0010\u0004\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\rR\u0016\u0010\u0005\u001a\u00020\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\rR\u0011\u0010\u0006\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0010\u0010\rR\u0016\u0010\u0007\u001a\u00020\b8\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0011\u0010\u0012R\u0013\u0010\t\u001a\u0004\u0018\u00010\u0001¢\u0006\b\n\u0000\u001a\u0004\b\u0013\u0010\u0014¨\u0006\""}, d2 = {"Lcom/Jayboys/PlaybackDecryptSource;", "", "quality", "", "label", "mimeType", "url", "bitrateKbps", "", "height", "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;JLjava/lang/Object;)V", "getQuality", "()Ljava/lang/String;", "getLabel", "getMimeType", "getUrl", "getBitrateKbps", "()J", "getHeight", "()Ljava/lang/Object;", "component1", "component2", "component3", "component4", "component5", "component6", "copy", "equals", "", "other", "hashCode", "", "toString", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class PlaybackDecryptSource {

    @com.fasterxml.jackson.annotation.JsonProperty("bitrate_kbps")
    private final long bitrateKbps;

    @org.jetbrains.annotations.Nullable
    private final java.lang.Object height;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String label;

    @com.fasterxml.jackson.annotation.JsonProperty("mime_type")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String mimeType;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String quality;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String url;

    public static /* synthetic */ com.Jayboys.PlaybackDecryptSource copy$default(com.Jayboys.PlaybackDecryptSource playbackDecryptSource, java.lang.String str, java.lang.String str2, java.lang.String str3, java.lang.String str4, long j, java.lang.Object obj, int i, java.lang.Object obj2) {
        if ((i & 1) != 0) {
            str = playbackDecryptSource.quality;
        }
        if ((i & 2) != 0) {
            str2 = playbackDecryptSource.label;
        }
        if ((i & 4) != 0) {
            str3 = playbackDecryptSource.mimeType;
        }
        if ((i & 8) != 0) {
            str4 = playbackDecryptSource.url;
        }
        if ((i & 16) != 0) {
            j = playbackDecryptSource.bitrateKbps;
        }
        if ((i & 32) != 0) {
            obj = playbackDecryptSource.height;
        }
        java.lang.Object obj3 = obj;
        long j2 = j;
        return playbackDecryptSource.copy(str, str2, str3, str4, j2, obj3);
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getQuality() {
        return this.quality;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getLabel() {
        return this.label;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final java.lang.String getMimeType() {
        return this.mimeType;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component4, reason: from getter */
    public final java.lang.String getUrl() {
        return this.url;
    }

    /* JADX INFO: renamed from: component5, reason: from getter */
    public final long getBitrateKbps() {
        return this.bitrateKbps;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component6, reason: from getter */
    public final java.lang.Object getHeight() {
        return this.height;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.PlaybackDecryptSource copy(@org.jetbrains.annotations.NotNull java.lang.String quality, @org.jetbrains.annotations.NotNull java.lang.String label, @com.fasterxml.jackson.annotation.JsonProperty("mime_type") @org.jetbrains.annotations.NotNull java.lang.String mimeType, @org.jetbrains.annotations.NotNull java.lang.String url, @com.fasterxml.jackson.annotation.JsonProperty("bitrate_kbps") long bitrateKbps, @org.jetbrains.annotations.Nullable java.lang.Object height) {
        return new com.Jayboys.PlaybackDecryptSource(quality, label, mimeType, url, bitrateKbps, height);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.Jayboys.PlaybackDecryptSource)) {
            return false;
        }
        com.Jayboys.PlaybackDecryptSource playbackDecryptSource = (com.Jayboys.PlaybackDecryptSource) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.quality, playbackDecryptSource.quality) && kotlin.jvm.internal.Intrinsics.areEqual(this.label, playbackDecryptSource.label) && kotlin.jvm.internal.Intrinsics.areEqual(this.mimeType, playbackDecryptSource.mimeType) && kotlin.jvm.internal.Intrinsics.areEqual(this.url, playbackDecryptSource.url) && this.bitrateKbps == playbackDecryptSource.bitrateKbps && kotlin.jvm.internal.Intrinsics.areEqual(this.height, playbackDecryptSource.height);
    }

    public int hashCode() {
        return (((((((((this.quality.hashCode() * 31) + this.label.hashCode()) * 31) + this.mimeType.hashCode()) * 31) + this.url.hashCode()) * 31) + com.Jayboys.PlaybackDecryptSource$$ExternalSyntheticBackport0.m(this.bitrateKbps)) * 31) + (this.height == null ? 0 : this.height.hashCode());
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "PlaybackDecryptSource(quality=" + this.quality + ", label=" + this.label + ", mimeType=" + this.mimeType + ", url=" + this.url + ", bitrateKbps=" + this.bitrateKbps + ", height=" + this.height + ')';
    }

    public PlaybackDecryptSource(@org.jetbrains.annotations.NotNull java.lang.String quality, @org.jetbrains.annotations.NotNull java.lang.String label, @com.fasterxml.jackson.annotation.JsonProperty("mime_type") @org.jetbrains.annotations.NotNull java.lang.String mimeType, @org.jetbrains.annotations.NotNull java.lang.String url, @com.fasterxml.jackson.annotation.JsonProperty("bitrate_kbps") long bitrateKbps, @org.jetbrains.annotations.Nullable java.lang.Object height) {
        this.quality = quality;
        this.label = label;
        this.mimeType = mimeType;
        this.url = url;
        this.bitrateKbps = bitrateKbps;
        this.height = height;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getQuality() {
        return this.quality;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getLabel() {
        return this.label;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getMimeType() {
        return this.mimeType;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getUrl() {
        return this.url;
    }

    public final long getBitrateKbps() {
        return this.bitrateKbps;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.Object getHeight() {
        return this.height;
    }
}
