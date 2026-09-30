package com.Gaycock4U;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\"\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\n\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B\u001b\u0012\b\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\b\u0010\u0004\u001a\u0004\u0018\u00010\u0003¢\u0006\u0004\b\u0005\u0010\u0006J\u000b\u0010\n\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u000b\u001a\u0004\u0018\u00010\u0003HÆ\u0003J!\u0010\f\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0003HÆ\u0001J\u0014\u0010\r\u001a\u00020\u000e2\b\u0010\u000f\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0010\u001a\u00020\u0011HÖ\u0081\u0004J\n\u0010\u0012\u001a\u00020\u0003HÖ\u0081\u0004R\u0013\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0007\u0010\bR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0003¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\b¨\u0006\u0013"}, d2 = {"Lcom/Gaycock4U/VideoSource;", "", "file", "", "label", "<init>", "(Ljava/lang/String;Ljava/lang/String;)V", "getFile", "()Ljava/lang/String;", "getLabel", "component1", "component2", "copy", "equals", "", "other", "hashCode", "", "toString", "Gaycock4U"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class VideoSource {

    @org.jetbrains.annotations.Nullable
    private final java.lang.String file;

    @org.jetbrains.annotations.Nullable
    private final java.lang.String label;

    public static /* synthetic */ com.Gaycock4U.VideoSource copy$default(com.Gaycock4U.VideoSource videoSource, java.lang.String str, java.lang.String str2, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            str = videoSource.file;
        }
        if ((i & 2) != 0) {
            str2 = videoSource.label;
        }
        return videoSource.copy(str, str2);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getFile() {
        return this.file;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getLabel() {
        return this.label;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Gaycock4U.VideoSource copy(@org.jetbrains.annotations.Nullable java.lang.String file, @org.jetbrains.annotations.Nullable java.lang.String label) {
        return new com.Gaycock4U.VideoSource(file, label);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.Gaycock4U.VideoSource)) {
            return false;
        }
        com.Gaycock4U.VideoSource videoSource = (com.Gaycock4U.VideoSource) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.file, videoSource.file) && kotlin.jvm.internal.Intrinsics.areEqual(this.label, videoSource.label);
    }

    public int hashCode() {
        return ((this.file == null ? 0 : this.file.hashCode()) * 31) + (this.label != null ? this.label.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "VideoSource(file=" + this.file + ", label=" + this.label + ')';
    }

    public VideoSource(@org.jetbrains.annotations.Nullable java.lang.String file, @org.jetbrains.annotations.Nullable java.lang.String label) {
        this.file = file;
        this.label = label;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getFile() {
        return this.file;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.String getLabel() {
        return this.label;
    }
}
